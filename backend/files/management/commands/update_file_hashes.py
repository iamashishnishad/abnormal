from django.core.management.base import BaseCommand
from files.models import File
import logging
from django.core.files import File
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update file_hash for existing files and handle duplicates'

    def handle(self, *args, **kwargs):
        files = File.objects.all()  # Process all files to ensure deduplication
        total_files = files.count()
        updated = 0
        duplicates_found = 0

        for file_obj in files:
            try:
                # Calculate file_hash if missing
                if not file_obj.file_hash:
                    file_hash = file_obj.calculate_file_hash()
                    if file_hash:
                        file_obj.file_hash = file_hash
                        logger.info(f"Set file_hash for {file_obj.original_filename}: {file_hash}")
                    else:
                        logger.warning(f"Could not calculate file_hash for {file_obj.original_filename}")
                        continue
                else:
                    file_hash = file_obj.file_hash

                # Check for duplicates
                existing_file = File.objects.filter(file_hash=file_hash).exclude(id=file_obj.id).first()
                if existing_file and not file_obj.is_duplicate:
                    logger.info(f"Duplicate found for {file_obj.original_filename}: original is {existing_file.original_filename}")
                    file_obj.is_duplicate = True
                    file_obj.original_file = existing_file
                    file_obj.storage_saved = file_obj.size
                    file_obj.file = File(existing_file.file, name=os.path.basename(existing_file.file.name))
                    existing_file.duplicate_count = File.objects.filter(original_file=existing_file).count() + 1
                    existing_file.save()
                    file_obj.save()
                    duplicates_found += 1
                    updated += 1
                elif file_obj.file_hash:
                    file_obj.save()  # Save to ensure file_hash is updated
                    updated += 1

            except Exception as e:
                logger.error(f"Error updating {file_obj.original_filename}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} of {total_files} files, found {duplicates_found} duplicates"))