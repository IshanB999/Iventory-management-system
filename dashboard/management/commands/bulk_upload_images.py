import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from dashboard.models import Products

class Command(BaseCommand):
    help = "Bulk upload product images based on filenames"

    def handle(self, *args, **kwargs):
        image_folder = os.path.join(settings.MEDIA_ROOT, 'product_images_bulk')

        if not os.path.exists(image_folder):
            self.stdout.write(self.style.ERROR(f"Folder {image_folder} does not exist"))
            return

        for product in Products.objects.all():
            image_found = False
            for ext in ['jpg', 'jpeg', 'png']:
                filename = f"{product.name}.{ext}"
                filepath = os.path.join(image_folder, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        product.image.save(filename, File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Image assigned to {product.name}"))
                    image_found = True
                    break
            if not image_found:
                self.stdout.write(self.style.WARNING(f"No image found for {product.name}"))
