WTForms-SQLAlchemy
==================

.. module:: wtforms_sqlalchemy


This module provides SelectField integration with SQLAlchemy ORM models,
similar to those in the Django extension.


ORM-backed fields
~~~~~~~~~~~~~~~~~
.. module:: wtforms_sqlalchemy.fields

These fields are provided to make it easier to use data from ORM objects in
your forms.

.. code-block:: python

    def enabled_categories():
        return Category.query.filter_by(enabled=True)

    class BlogPostEdit(Form):
        title    = StringField()
        blog     = QuerySelectField(get_label='title')
        category = QuerySelectField(query_factory=enabled_categories, allow_blank=True)

    def edit_blog_post(request, id):
        post = Post.query.get(id)
        form = BlogPostEdit(obj=post)
        # Since we didn't provide a query_factory for the 'blog' field, we need
        # to set a dynamic one in the view.
        form.blog.query = Blog.query.filter(Blog.author == request.user).order_by(Blog.name)


.. autoclass:: QuerySelectField(default field args, query_factory=None, get_pk=None, get_label=None, allow_blank=False, blank_text=u'')

.. autoclass:: QuerySelectMultipleField(default field args, query_factory=None, get_pk=None, get_label=None)


Model forms
~~~~~~~~~~~
.. module:: wtforms_sqlalchemy.orm

It is possible to generate forms from SQLAlchemy models similarly to how it can be done for Django ORM models.

.. autofunction:: model_form
