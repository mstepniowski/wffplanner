# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'Movie'
        db.create_table('movies_movie', (
            ('url', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('info', self.gf('movies.fields.JSONField')(default='{}', json_type=dict)),
        ))
        db.send_create_signal('movies', ['Movie'])

        # Adding model 'Screening'
        db.create_table('movies_screening', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('movie', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['movies.Movie'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('room', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('movies', ['Screening'])


    def backwards(self, orm):
        db.delete_table('movies_movie')
        db.delete_table('movies_screening')

    models = {
        'movies.movie': {
            'Meta': {'object_name': 'Movie'},
            'info': ('movies.fields.JSONField', [], {'default': "'{}'", 'json_type': 'dict'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        },
        'movies.screening': {
            'Meta': {'object_name': 'Screening'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'movie': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['movies.Movie']"}),
            'room': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        }
    }

    complete_apps = ['movies']
