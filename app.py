import os

from flask import Flask, render_template, url_for
from flask_admin import Admin, form
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup

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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image = db.Column(db.Unicode(128), nullable=False)

    def __repr__(self):
        return '<Cactus %r>' % self.name


class CactusModelView(ModelView):
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


admin = Admin(app, name='cacti', template_mode='bootstrap3')
admin.add_view(CactusModelView(Cactus, db.session))


@app.route('/')
def index():
    cacti = Cactus.query.all()
    return render_template('index.html', cacti=cacti, thumbnail=form.thumbgen_filename)


@app.route('/cacti/<int:pk>')
def detail(pk):
    cactus = Cactus.query.filter_by(id=pk).first()
    return render_template('detail.html', cactus=cactus)


if __name__ == '__main__':
    app.run()
