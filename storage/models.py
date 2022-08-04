from django.db import models


class PathMapping(models.Model):
    filename = models.CharField(max_length=255, db_index=True)
    filepath = models.FilePathField()
    filesize = models.IntegerField()
    fileid = models.CharField(max_length=255, db_index=True)
    message_id = models.CharField(max_length=64, db_index=True)
    up_path = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    accessed = models.DateTimeField(auto_now=True)

    def update_accessed(self):
        modified = self.modified

        self.save()
        PathMapping.objects.filter(id=self.id).update(modified=modified)
