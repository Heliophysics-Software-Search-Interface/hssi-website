class WebsiteRouter:

    """
    A router to control all database operations on models in the
    website application.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read website models go to the website database.
        """
        if model._meta.app_label == 'website':
            return 'website'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write website models go to the website database.
        """
        if model._meta.app_label == 'website':
            return 'website'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the website app is involved.
        """
        if obj1._meta.app_label == 'website' or \
            obj2._meta.app_label == 'website':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the website app only appears in the website database.
        """
        if app_label == 'website':
            return db == 'website'
        return None