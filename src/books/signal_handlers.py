from django.db.models.signals import post_delete
from django.dispatch import receiver

from books.models import Book, BookDetails


@receiver(post_delete, sender=Book)
def delete_related_book_details(sender, instance, **kwargs):
    if instance.details_id is not None:
        # It won't exist if we're deleting the BookDetails directly
        details = BookDetails.objects.filter(pk=instance.details_id).first()
        if details:
            details.delete()
