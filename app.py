import os

from flask import Flask, render_template, url_for
from flask_admin import Admin, form
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from sqlalchemy_utils import ChoiceType
from werkzeug.exceptions import NotFound
from wtforms import TextAreaField
from wtforms.widgets import TextArea

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['SECRET_KEY'] = 'So secret such key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

file_path = os.path.join(os.path.dirname(__file__), 'static')
try:
    os.mkdir(file_path)
except OSError:
    pass


class Cactus(db.Model):
    LOW = 'Низкая'
    MEDIUM = 'Средняя'
    HIGH = 'Высокая'
    DIFFICULTY = (
        (1, LOW),
        (2, MEDIUM),
        (3, HIGH),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image = db.Column(db.Unicode(128), nullable=False)
    difficulty = db.Column(ChoiceType(DIFFICULTY), nullable=True)
    products = db.relationship('RelatedProduct', backref='cactus', lazy=True)

    def __repr__(self):
        return '<Cactus %r>' % self.name


class RelatedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image = db.Column(db.Unicode(128), nullable=False)
    cactus_id = db.Column(db.Integer, db.ForeignKey('cactus.id'), nullable=False)

    def __repr__(self):
        return '<RelatedProduct %r>' % self.name


class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()


class CustomModelView(ModelView):
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']

    def _list_thumbnail(view, context, model, name):
        if not model.path:
            return ''

        filename = form.thumbgen_filename(model.path)
        url = url_for('static', filename=filename)

        return Markup(f'<img src="{url}">')

    column_formatters = {
        'path': _list_thumbnail
    }

    form_extra_fields = {
        'image': form.ImageUploadField(
            'Image',
            base_path=file_path,
            thumbnail_size=(320, 320, True),
        )
    }

    form_overrides = {
        'description': CKTextAreaField,
    }


admin = Admin(app, name='cacti', template_mode='bootstrap3')
admin.add_view(CustomModelView(Cactus, db.session))
admin.add_view(CustomModelView(RelatedProduct, db.session))


@app.route('/')
def index():
    cacti = Cactus.query.all()
    return render_template('index.html', cacti=cacti, thumbnail=form.thumbgen_filename)


@app.route('/route/<int:pk>')
def detail(pk):
    cactus = Cactus.query.filter_by(id=pk).first()
    if not cactus:
        raise NotFound
    return render_template('detail.html', cactus=cactus)


if __name__ == '__main__':
    app.run()
