from unittest import TestCase
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from wtforms_sqlalchemy.orm import model_form
from wtforms_sqlalchemy.orm import ModelConversionError
from wtforms_sqlalchemy.orm import ModelConverter

from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import types as sqla_types
from sqlalchemy.dialects.mssql import BIT
from sqlalchemy.dialects.mysql import YEAR
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import MACADDR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.schema import ColumnDefault
from sqlalchemy.schema import MetaData
from sqlalchemy.schema import Table
from wtforms import fields
from wtforms import Form
from wtforms.compat import iteritems
from wtforms.compat import text_type
from wtforms.validators import Optional
from wtforms.validators import Regexp
from wtforms.validators import Required

from .common import contains_validator
from .common import DummyPostData


class LazySelect:
    def __call__(self, field, **kwargs):
        return list(
            (val, text_type(label), selected)
            for val, label, selected in field.iter_choices()
        )


class Base:
    def __init__(self, **kwargs):
        for k, v in iteritems(kwargs):
            setattr(self, k, v)


class AnotherInteger(sqla_types.Integer):
    """Use me to test if MRO works like we want"""


class TestBase(TestCase):
    def _do_tables(self, mapper, engine):
        metadata = MetaData()

        test_table = Table(
            "test",
            metadata,
            Column("id", sqla_types.Integer, primary_key=True, nullable=False),
            Column("name", sqla_types.String, nullable=False),
        )

        pk_test_table = Table(
            "pk_test",
            metadata,
            Column("foobar", sqla_types.String, primary_key=True, nullable=False),
            Column("baz", sqla_types.String, nullable=False),
        )

        Test = type("Test", (Base,), {})
        PKTest = type(
            "PKTest",
            (Base,),
            {"__unicode__": lambda x: x.baz, "__str__": lambda x: x.baz},
        )

        mapper(Test, test_table, order_by=[test_table.c.name])
        mapper(PKTest, pk_test_table, order_by=[pk_test_table.c.baz])
        self.Test = Test
        self.PKTest = PKTest

        metadata.create_all(bind=engine)

    def _fill(self, sess):
        for i, n in [(1, "apple"), (2, "banana")]:
            s = self.Test(id=i, name=n)
            p = self.PKTest(foobar=f"hello{i}", baz=n)
            sess.add(s)
            sess.add(p)
        sess.flush()
        sess.commit()


class QuerySelectFieldTest(TestBase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", echo=False)
        self.Session = sessionmaker(bind=engine)
        from sqlalchemy.orm import mapper

        self._do_tables(mapper, engine)

    def test_without_factory(self):
        sess = self.Session()
        self._fill(sess)

        class F(Form):
            a = QuerySelectField(
                get_label="name", widget=LazySelect(), get_pk=lambda x: x.id
            )

        form = F(DummyPostData(a=["1"]))
        form.a.query = sess.query(self.Test)
        self.assertTrue(form.a.data is not None)
        self.assertEqual(form.a.data.id, 1)
        self.assertEqual(form.a(), [("1", "apple", True), ("2", "banana", False)])
        self.assertTrue(form.validate())

        form = F(a=sess.query(self.Test).filter_by(name="banana").first())
        form.a.query = sess.query(self.Test).filter(self.Test.name != "banana")
        assert not form.validate()
        self.assertEqual(form.a.errors, ["Not a valid choice"])

        # Test query with no results
        form = F()
        form.a.query = (
            sess.query(self.Test).filter(self.Test.id == 1, self.Test.id != 1).all()
        )
        self.assertEqual(form.a(), [])

    def test_with_query_factory(self):
        sess = self.Session()
        self._fill(sess)

        class F(Form):
            a = QuerySelectField(
                get_label=(lambda model: model.name),
                query_factory=lambda: sess.query(self.Test),
                widget=LazySelect(),
            )
            b = QuerySelectField(
                allow_blank=True,
                query_factory=lambda: sess.query(self.PKTest),
                widget=LazySelect(),
            )

        form = F()
        self.assertEqual(form.a.data, None)
        self.assertEqual(form.a(), [("1", "apple", False), ("2", "banana", False)])
        self.assertEqual(form.b.data, None)
        self.assertEqual(
            form.b(),
            [
                ("__None", "", True),
                ("hello1", "apple", False),
                ("hello2", "banana", False),
            ],
        )
        self.assertFalse(form.validate())

        form = F(DummyPostData(a=["1"], b=["hello2"]))
        self.assertEqual(form.a.data.id, 1)
        self.assertEqual(form.a(), [("1", "apple", True), ("2", "banana", False)])
        self.assertEqual(form.b.data.baz, "banana")
        self.assertEqual(
            form.b(),
            [
                ("__None", "", False),
                ("hello1", "apple", False),
                ("hello2", "banana", True),
            ],
        )
        self.assertTrue(form.validate())

        # Make sure the query is cached
        sess.add(self.Test(id=3, name="meh"))
        sess.flush()
        sess.commit()
        self.assertEqual(form.a(), [("1", "apple", True), ("2", "banana", False)])
        form.a._object_list = None
        self.assertEqual(
            form.a(),
            [("1", "apple", True), ("2", "banana", False), ("3", "meh", False)],
        )

        # Test bad data
        form = F(DummyPostData(b=["__None"], a=["fail"]))
        assert not form.validate()
        self.assertEqual(form.a.errors, ["Not a valid choice"])
        self.assertEqual(form.b.errors, [])
        self.assertEqual(form.b.data, None)

        # Test query with no results
        form = F()
        form.a.query = (
            sess.query(self.Test).filter(self.Test.id == 1, self.Test.id != 1).all()
        )
        self.assertEqual(form.a(), [])


class QuerySelectMultipleFieldTest(TestBase):
    def setUp(self):
        from sqlalchemy.orm import mapper

        engine = create_engine("sqlite:///:memory:", echo=False)
        Session = sessionmaker(bind=engine)
        self._do_tables(mapper, engine)
        self.sess = Session()
        self._fill(self.sess)

    class F(Form):
        a = QuerySelectMultipleField(get_label="name", widget=LazySelect())

    def test_unpopulated_default(self):
        form = self.F()
        self.assertEqual([], form.a.data)

    def test_single_value_without_factory(self):
        form = self.F(DummyPostData(a=["1"]))
        form.a.query = self.sess.query(self.Test)
        self.assertEqual([1], [v.id for v in form.a.data])
        self.assertEqual(form.a(), [("1", "apple", True), ("2", "banana", False)])
        self.assertTrue(form.validate())

    def test_multiple_values_without_query_factory(self):
        form = self.F(DummyPostData(a=["1", "2"]))
        form.a.query = self.sess.query(self.Test)
        self.assertEqual([1, 2], [v.id for v in form.a.data])
        self.assertEqual(form.a(), [("1", "apple", True), ("2", "banana", True)])
        self.assertTrue(form.validate())

        form = self.F(DummyPostData(a=["1", "3"]))
        form.a.query = self.sess.query(self.Test)
        self.assertEqual([x.id for x in form.a.data], [1])
        self.assertFalse(form.validate())

    def test_single_default_value(self):
        first_test = self.sess.query(self.Test).get(2)

        class F(Form):
            a = QuerySelectMultipleField(
                get_label="name",
                default=[first_test],
                widget=LazySelect(),
                query_factory=lambda: self.sess.query(self.Test),
            )

        form = F()
        self.assertEqual([v.id for v in form.a.data], [2])
        self.assertEqual(form.a(), [("1", "apple", False), ("2", "banana", True)])
        self.assertTrue(form.validate())


class ModelFormTest(TestCase):
    def setUp(self):
        Model = declarative_base()

        student_course = Table(
            "student_course",
            Model.metadata,
            Column("student_id", sqla_types.Integer, ForeignKey("student.id")),
            Column("course_id", sqla_types.Integer, ForeignKey("course.id")),
        )

        class Course(Model):
            __tablename__ = "course"
            id = Column(sqla_types.Integer, primary_key=True)
            name = Column(sqla_types.String(255), nullable=False)
            # These are for better model form testing
            cost = Column(sqla_types.Numeric(5, 2), nullable=False)
            description = Column(sqla_types.Text, nullable=False)
            level = Column(sqla_types.Enum("Primary", "Secondary"))
            has_prereqs = Column(sqla_types.Boolean, nullable=False)
            boolean_nullable = Column(sqla_types.Boolean, nullable=True)
            started = Column(sqla_types.DateTime, nullable=False)
            grade = Column(AnotherInteger, nullable=False)

        class School(Model):
            __tablename__ = "school"
            id = Column(sqla_types.Integer, primary_key=True)
            name = Column(sqla_types.String(255), nullable=False)

        class Student(Model):
            __tablename__ = "student"
            id = Column(sqla_types.Integer, primary_key=True)
            full_name = Column(sqla_types.String(255), nullable=False, unique=True)
            dob = Column(sqla_types.Date(), nullable=True)
            current_school_id = Column(
                sqla_types.Integer, ForeignKey(School.id), nullable=False
            )

            current_school = relationship(School, backref=backref("students"))
            courses = relationship(
                "Course",
                secondary=student_course,
                backref=backref("students", lazy="dynamic"),
            )

        self.School = School
        self.Student = Student
        self.Course = Course

        engine = create_engine("sqlite:///:memory:", echo=False)
        Session = sessionmaker(bind=engine)
        self.metadata = Model.metadata
        self.metadata.create_all(bind=engine)
        self.sess = Session()

    def test_auto_validators(self):
        course_form = model_form(self.Course, self.sess)()
        student_form = model_form(self.Student, self.sess)()
        assert contains_validator(student_form.dob, Optional)
        assert contains_validator(student_form.full_name, Required)
        assert not contains_validator(course_form.has_prereqs, Optional)
        assert contains_validator(course_form.has_prereqs, Required)
        assert contains_validator(course_form.boolean_nullable, Optional)
        assert not contains_validator(course_form.boolean_nullable, Required)

    def test_field_args(self):
        shared = {"full_name": {"validators": [Regexp("test")]}}
        student_form = model_form(self.Student, self.sess, field_args=shared)()
        assert contains_validator(student_form.full_name, Regexp)

        # original shared field_args should not be modified
        assert len(shared["full_name"]["validators"]) == 1

    def test_include_pk(self):
        form_class = model_form(self.Student, self.sess, exclude_pk=False)
        student_form = form_class()
        assert "id" in student_form._fields

    def test_exclude_pk(self):
        form_class = model_form(self.Student, self.sess, exclude_pk=True)
        student_form = form_class()
        assert "id" not in student_form._fields

    def test_exclude_fk(self):
        student_form = model_form(self.Student, self.sess)()
        assert "current_school_id" not in student_form._fields

    def test_include_fk(self):
        student_form = model_form(self.Student, self.sess, exclude_fk=False)()
        assert "current_school_id" in student_form._fields

    def test_convert_many_to_one(self):
        student_form = model_form(self.Student, self.sess)()
        assert isinstance(student_form.current_school, QuerySelectField)

    def test_convert_one_to_many(self):
        school_form = model_form(self.School, self.sess)()
        assert isinstance(school_form.students, QuerySelectMultipleField)

    def test_convert_many_to_many(self):
        student_form = model_form(self.Student, self.sess)()
        assert isinstance(student_form.courses, QuerySelectMultipleField)

    def test_convert_basic(self):
        self.assertRaises(TypeError, model_form, None)
        self.assertRaises(ModelConversionError, model_form, self.Course)
        form_class = model_form(self.Course, exclude=["students"])
        form = form_class()
        self.assertEqual(len(list(form)), 8)

    def test_only(self):
        desired_fields = ["id", "cost", "description"]
        form = model_form(self.Course, only=desired_fields)()
        self.assertEqual(len(list(form)), 2)
        form = model_form(self.Course, only=desired_fields, exclude_pk=False)()
        self.assertEqual(len(list(form)), 3)

    def test_no_mro(self):
        converter = ModelConverter(use_mro=False)
        # Without MRO, will not be able to convert 'grade'
        self.assertRaises(
            ModelConversionError,
            model_form,
            self.Course,
            self.sess,
            converter=converter,
        )
        # If we exclude 'grade' everything should continue working
        F = model_form(self.Course, self.sess, exclude=["grade"], converter=converter)
        self.assertEqual(len(list(F())), 8)


class ModelFormColumnDefaultTest(TestCase):
    def setUp(self):
        Model = declarative_base()

        def default_score():
            return 5

        class StudentDefaultScoreCallable(Model):
            __tablename__ = "course"
            id = Column(sqla_types.Integer, primary_key=True)
            name = Column(sqla_types.String(255), nullable=False)
            score = Column(sqla_types.Integer, default=default_score, nullable=False)

        class StudentDefaultScoreScalar(Model):
            __tablename__ = "school"
            id = Column(sqla_types.Integer, primary_key=True)
            name = Column(sqla_types.String(255), nullable=False)
            # Default scalar value
            score = Column(sqla_types.Integer, default=10, nullable=False)

        self.StudentDefaultScoreCallable = StudentDefaultScoreCallable
        self.StudentDefaultScoreScalar = StudentDefaultScoreScalar

        engine = create_engine("sqlite:///:memory:", echo=False)
        Session = sessionmaker(bind=engine)
        self.metadata = Model.metadata
        self.metadata.create_all(bind=engine)
        self.sess = Session()

    def test_column_default_callable(self):
        student_form = model_form(self.StudentDefaultScoreCallable, self.sess)()
        self.assertEqual(student_form._fields["score"].default, 5)

    def test_column_default_scalar(self):
        student_form = model_form(self.StudentDefaultScoreScalar, self.sess)()
        assert not isinstance(student_form._fields["score"].default, ColumnDefault)
        self.assertEqual(student_form._fields["score"].default, 10)


class ModelFormTest2(TestCase):
    def setUp(self):
        Model = declarative_base()

        class AllTypesModel(Model):
            __tablename__ = "course"
            id = Column(sqla_types.Integer, primary_key=True)
            string = Column(sqla_types.String)
            unicode = Column(sqla_types.Unicode)
            varchar = Column(sqla_types.VARCHAR)
            integer = Column(sqla_types.Integer)
            biginteger = Column(sqla_types.BigInteger)
            smallinteger = Column(sqla_types.SmallInteger)
            numeric = Column(sqla_types.Numeric)
            float = Column(sqla_types.Float)
            text = Column(sqla_types.Text)
            binary = Column(sqla_types.Binary)
            largebinary = Column(sqla_types.LargeBinary)
            unicodetext = Column(sqla_types.UnicodeText)
            enum = Column(sqla_types.Enum("Primary", "Secondary"))
            boolean = Column(sqla_types.Boolean)
            datetime = Column(sqla_types.DateTime)
            timestamp = Column(sqla_types.TIMESTAMP)
            date = Column(sqla_types.Date)
            postgres_inet = Column(INET)
            postgres_macaddr = Column(MACADDR)
            postgres_uuid = Column(UUID)
            mysql_year = Column(YEAR)
            mssql_bit = Column(BIT)

        self.AllTypesModel = AllTypesModel

    def test_convert_types(self):
        form = model_form(self.AllTypesModel)()

        assert isinstance(form.string, fields.StringField)
        assert isinstance(form.unicode, fields.StringField)
        assert isinstance(form.varchar, fields.StringField)
        assert isinstance(form.postgres_inet, fields.StringField)
        assert isinstance(form.postgres_macaddr, fields.StringField)
        assert isinstance(form.postgres_uuid, fields.StringField)
        assert isinstance(form.mysql_year, fields.StringField)

        assert isinstance(form.integer, fields.IntegerField)
        assert isinstance(form.biginteger, fields.IntegerField)
        assert isinstance(form.smallinteger, fields.IntegerField)

        assert isinstance(form.numeric, fields.DecimalField)
        assert isinstance(form.float, fields.DecimalField)

        assert isinstance(form.text, fields.TextAreaField)
        assert isinstance(form.binary, fields.TextAreaField)
        assert isinstance(form.largebinary, fields.TextAreaField)
        assert isinstance(form.unicodetext, fields.TextAreaField)

        assert isinstance(form.enum, fields.SelectField)

        assert isinstance(form.boolean, fields.BooleanField)
        assert isinstance(form.mssql_bit, fields.BooleanField)

        assert isinstance(form.datetime, fields.DateTimeField)
        assert isinstance(form.timestamp, fields.DateTimeField)

        assert isinstance(form.date, fields.DateField)
