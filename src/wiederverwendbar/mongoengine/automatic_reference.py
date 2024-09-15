from enum import Enum

from bson import ObjectId
from mongoengine import signals, Document, ListField, ReferenceField
from mongoengine.base import TopLevelDocumentMetaclass


class AutomaticReferenceTypes(Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class AutomaticReferenceDocumentMeta(TopLevelDocumentMetaclass):
    def __new__(mcs, name, bases, attrs):
        # add attribute '_automatic_reference_fields' to class for caching
        attrs["_automatic_reference_fields"] = None

        # create new class
        new_class = super().__new__(mcs, name, bases, attrs)

        # connect signals
        signals.post_save.connect(mcs.post_save, sender=new_class)
        signals.pre_delete.connect(mcs.pre_delete, sender=new_class)

        return new_class

    @classmethod
    def get_automatic_reference_fields(cls, document) -> list[tuple[str, "AutomaticReferenceDocumentMeta", AutomaticReferenceTypes, str]]:
        # return cached reference fields
        automatic_reference_fields = getattr(document, "_automatic_reference_fields")
        if automatic_reference_fields is not None:
            return automatic_reference_fields

        # get all reference fields
        all_fields = getattr(document, "_fields")
        automatic_reference_fields = []
        for field_name in getattr(document, "_fields_ordered"):
            field = all_fields[field_name]
            automatic_reference = getattr(field, "automatic_reference", None)
            if automatic_reference is None:
                continue
            if not isinstance(field, ReferenceField) and not isinstance(field, ListField):
                continue

            # get reference field
            reference_field = None
            if isinstance(field, ReferenceField):
                reference_field = field
            elif isinstance(field, ListField):
                if not hasattr(field, "field"):
                    raise ValueError(f"ListField {field.name} has no field attribute.")
                if not isinstance(field.field, ReferenceField):
                    raise ValueError(f"ListField {field.name} has no ReferenceField as field attribute.")
                reference_field = field.field
            if reference_field is None:
                raise ValueError(f"Document type of field {field.name} can not be resolved.")

            # get document type
            document_type = getattr(reference_field, "document_type")
            if not isinstance(document_type, AutomaticReferenceDocumentMeta):
                raise ValueError(f"config field of {cls.__name__} can not be resolved to a document type.")

            # get automatic reference type
            reference_type = None
            field_from_reference = getattr(document_type, automatic_reference)
            field_from_reference_automatic_reference = getattr(field_from_reference, "automatic_reference")
            if field_from_reference_automatic_reference != field_name:
                raise ValueError(f"Automatic reference field {field_name} not found in document {document_type.__name__}.{automatic_reference}.")
            if isinstance(field, ReferenceField):
                if isinstance(field_from_reference, ReferenceField):  # ONE_TO_ONE
                    reference_type = AutomaticReferenceTypes.ONE_TO_ONE
                elif isinstance(field_from_reference, ListField):  # ONE_TO_MANY
                    reference_type = AutomaticReferenceTypes.ONE_TO_MANY
            elif isinstance(field, ListField):
                if isinstance(field_from_reference, ReferenceField):  # MANY_TO_ONE
                    reference_type = AutomaticReferenceTypes.MANY_TO_ONE
                elif isinstance(field_from_reference, ListField):  # MANY_TO_MANY
                    reference_type = AutomaticReferenceTypes.MANY_TO_MANY
            if reference_type is None:
                raise ValueError(f"Field type for field {field.name} not found.")

            automatic_reference_fields.append((field_name, document_type, reference_type, automatic_reference))

        # cache reference fields
        setattr(document, "_automatic_reference_fields", automatic_reference_fields)

        return automatic_reference_fields

    @classmethod
    def resolve_object_id(cls, document, field_name, field, reference_document):
        if type(field) is ObjectId:
            field = reference_document.objects(id=field).first()
            if field is None:
                raise ValueError(f"{reference_document.__name__} with id {getattr(document, field_name)} not found.")
            setattr(document, field_name, field)
        return field

    @classmethod
    def merge_and_save(cls, save_documents):
        # merge all documents
        merged_documents = []
        for reference_document, documents in save_documents.items():
            merged_documents_by_id = {}
            for document in documents:
                if document.id not in merged_documents_by_id:
                    merged_documents_by_id[document.id] = document
                else:
                    for changed_field in getattr(document, "_changed_fields"):
                        setattr(merged_documents_by_id[document.id], changed_field, getattr(document, changed_field))
            merged_documents.extend(merged_documents_by_id.values())

        # save merged documents
        for document in merged_documents:
            document.save()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        save_documents = {}
        # save all reference fields
        for field_name, reference_document, reference_type, reference_field_name in cls.get_automatic_reference_fields(document):
            if reference_document not in save_documents:
                save_documents[reference_document] = []
            if reference_type == AutomaticReferenceTypes.ONE_TO_ONE:
                save_documents[reference_document].extend(cls.save_one_to_one(document, field_name, reference_document, reference_field_name))
            elif reference_type == AutomaticReferenceTypes.ONE_TO_MANY:
                save_documents[reference_document].extend(cls.save_one_to_many(document, field_name, reference_document, reference_field_name))
            elif reference_type == AutomaticReferenceTypes.MANY_TO_ONE:
                save_documents[reference_document].extend(cls.save_many_to_one(document, field_name, reference_document, reference_field_name))
            elif reference_type == AutomaticReferenceTypes.MANY_TO_MANY:
                save_documents[reference_document].extend(cls.save_many_to_many(document, field_name, reference_document, reference_field_name))
            else:
                raise ValueError(f"Reference type {reference_type} not not supported.")

        # merge and save all documents
        cls.merge_and_save(save_documents)

    @classmethod
    def save_one_to_one(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # add document to reference field
        field = getattr(document, field_name)
        if field is not None:
            reference = cls.resolve_object_id(document, field_name, field, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document != reference_field:
                setattr(reference, reference_field_name, document)
                save_references.append(reference)
        # remove document from old reference field
        for reference in reference_document.objects(**{reference_field_name: document}):
            if field == reference:
                continue
            setattr(reference, reference_field_name, None)
            save_references.append(reference)
        return save_references

    @classmethod
    def save_one_to_many(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # add document to reference field
        field = getattr(document, field_name)
        if field is not None:
            reference = cls.resolve_object_id(document, field_name, field, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document not in reference_field:
                reference_field.append(document)
                setattr(reference, reference_field_name, reference_field)
                save_references.append(reference)
        # remove document from old reference field
        for reference in reference_document.objects(**{reference_field_name: document}):
            if reference == field:
                continue
            reference_field = getattr(reference, reference_field_name)
            reference_field.remove(document)
            setattr(reference, reference_field_name, reference_field)
            save_references.append(reference)
        return save_references

    @classmethod
    def save_many_to_one(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # add document to reference field
        field = getattr(document, field_name)
        for reference in field:
            reference = cls.resolve_object_id(document, field_name, reference, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document != reference_field:
                setattr(reference, reference_field_name, document)
                save_references.append(reference)
        # remove document from old reference field
        for reference in reference_document.objects(**{reference_field_name: document}):
            if reference in field:
                continue
            setattr(reference, reference_field_name, None)
            save_references.append(reference)
        return save_references

    @classmethod
    def save_many_to_many(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # add document to reference field
        field = getattr(document, field_name)
        for reference in field:
            reference = cls.resolve_object_id(document, field_name, reference, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document not in reference_field:
                reference_field.append(document)
                setattr(reference, reference_field_name, reference_field)
                save_references.append(reference)
        # remove document from old reference field
        for reference in reference_document.objects(**{reference_field_name: document}):
            if reference in field:
                continue
            reference_field = getattr(reference, reference_field_name)
            reference_field.remove(document)
            setattr(reference, reference_field_name, reference_field)
            save_references.append(reference)
        return save_references

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        save_documents = {}
        # delete all reference fields
        for field_name, reference_document, reference_type, reference_field_name in cls.get_automatic_reference_fields(document):
            if reference_document not in save_documents:
                save_documents[reference_document] = []
            if reference_type == AutomaticReferenceTypes.ONE_TO_ONE:
                save_documents[reference_document].extend(cls.delete_one_to_one(document, field_name, reference_document, reference_field_name))
            elif reference_type == AutomaticReferenceTypes.ONE_TO_MANY:
                save_documents[reference_document].extend(cls.delete_one_to_many(document, field_name, reference_document, reference_field_name))
            elif reference_type == AutomaticReferenceTypes.MANY_TO_ONE:
                save_documents[reference_document].extend(cls.delete_many_to_one(document, field_name, reference_document, reference_field_name))
            elif reference_type == AutomaticReferenceTypes.MANY_TO_MANY:
                save_documents[reference_document].extend(cls.delete_many_to_many(document, field_name, reference_document, reference_field_name))
            else:
                raise ValueError(f"Reference type {reference_type} not not supported.")

        # merge and save all documents
        cls.merge_and_save(save_documents)

    @classmethod
    def delete_one_to_one(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # remove document from reference field
        field = getattr(document, field_name)
        if field is not None:
            reference = cls.resolve_object_id(document, field_name, field, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document == reference_field:
                setattr(reference, reference_field_name, None)
                save_references.append(reference)
        return save_references

    @classmethod
    def delete_one_to_many(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # remove document from reference field
        field = getattr(document, field_name)
        if field is not None:
            reference = cls.resolve_object_id(document, field_name, field, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document in reference_field:
                reference_field.remove(document)
                setattr(reference, reference_field_name, reference_field)
                save_references.append(reference)
        return save_references

    @classmethod
    def delete_many_to_one(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # remove document from reference field
        field = getattr(document, field_name)
        for reference in field:
            reference = cls.resolve_object_id(document, field_name, reference, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document == reference_field:
                setattr(reference, reference_field_name, None)
                save_references.append(reference)
        return save_references

    @classmethod
    def delete_many_to_many(cls, document, field_name, reference_document, reference_field_name) -> list["AutomaticReferenceDocumentMeta"]:
        save_references = []
        # remove document from reference field
        field = getattr(document, field_name)
        for reference in field:
            reference = cls.resolve_object_id(document, field_name, reference, reference_document)
            reference_field = getattr(reference, reference_field_name)
            if document in reference_field:
                reference_field.remove(document)
                setattr(reference, reference_field_name, reference_field)
                save_references.append(reference)
        return save_references


class AutomaticReferenceDocument(Document, metaclass=AutomaticReferenceDocumentMeta):
    meta = {"abstract": True}
