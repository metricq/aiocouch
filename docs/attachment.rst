===========
Attachments
===========

Attachments are independent binary data attached to a document. They are file-like and require a
name and the content type. As attachments do not have size restrictions, they are handled a bit
differently than documents in the :class:`~aiocouch.document.Document` class. The content of the
attachment isn't cached in the instance at any point, thus data access require a network request.

Getting an Attachment instance
==============================

Given a document instance, we can get an Attachment instance using the
:meth:`~aiocouch.document.Document.attachment` member function. Unlike with
:class:`~aiocouch.document.Document` instances, no data is retrieved from the sever yet.

.. code-block :: python

    butterfly = await database["butterfly"]
    image_of_a_butterfly = butterfly.attachment("image.png")


Retrieving the Attachment content
=================================

To actually retrieve the data stored on the server, you have to use the
:meth:`~aiocouch.attachment.Attachment.fetch()` method. Once the fetch method is called, the
`content_type` member will be set to appropriate value passed from the server.

.. code-block :: python

    data = await image_of_a_butterfly.fetch()

Saving the content of an attachment
===================================



Reference
=========

.. autoclass:: aiocouch.attachment.Attachment
    :members:
