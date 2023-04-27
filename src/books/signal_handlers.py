from django.db.models.signals import post_delete
from django.dispatch import receiver

from books.models import Book, BookDetails


@receiver(post_delete, sender=Book)
def delete_related_book_details(sender, instance, **kwargs):
    if instance.details is not None:
        details = BookDetails.objects.get(pk=instance.details.pk)
        details.delete()
