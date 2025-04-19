from django.core.management.base import BaseCommand
from files.models import File
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update file_hash for existing files'

    def handle(self, *args, **kwargs):
        files = File.objects.filter(file_hash__isnull=True)
        total_files = files.count()
        updated = 0

        for file_obj in files:
            try:
                file_hash = file_obj.calculate_file_hash()
                if file_hash:
                    file_obj.file_hash = file_hash
                    # Check for duplicates
                    existing_file = File.objects.filter(file_hash=file_hash).exclude(id=file_obj.id).first()
                    if existing_file:
                        file_obj.is_duplicate = True
                        file_obj.original_file = existing_file
                        file_obj.storage_saved = file_obj.size
                        file_obj.file = File(existing_file.file, name=os.path.basename(existing_file.file.name))
                        existing_file.duplicate_count = File.objects.filter(original_file=existing_file).count() + 1
                        existing_file.save()
                    file_obj.save()
                    updated += 1
                    logger.info(f"Updated file_hash for {file_obj.original_filename}: {file_hash}")
                else:
                    logger.warning(f"Could not calculate file_hash for {file_obj.original_filename}")
            except Exception as e:
                logger.error(f"Error updating {file_obj.original_filename}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} of {total_files} files"))