import os

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_admin import Admin, form
from flask_admin import helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_migrate import Migrate
from flask_security import RoleMixin, SQLAlchemyUserDatastore, Security, UserMixin, hash_password
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from sqlalchemy_utils import ChoiceType, generic_relationship
from werkzeug.exceptions import NotFound, abort
from wtforms import TextAreaField
from wtforms.widgets import TextArea

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['SECRET_KEY'] = 'So secret such key'
app.config['SECURITY_PASSWORD_SALT'] = 'Some salt here'
app.config['SECURITY_REGISTERABLE'] = True
# app.config['UPLOAD_FOLDER'] = 'media'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

file_path = os.path.join(os.path.dirname(__file__), 'static', 'media')
try:
    os.mkdir(file_path)
except OSError:
    pass


class Cactus(db.Model):
    LOW = 'Низкая'
    MEDIUM = 'Средняя'
    HIGH = 'Высокая'
    DIFFICULTY = (
        ('1', LOW),
        ('2', MEDIUM),
        ('3', HIGH),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image = db.Column(db.Unicode(128), nullable=False)
    difficulty = db.Column(ChoiceType(DIFFICULTY), nullable=True)
    products = db.relationship('RelatedProduct', backref='cactus', lazy=True)

    @property
    def image_path(self):
        return f'media/{form.thumbgen_filename(self.image)}'

    def __repr__(self):
        return '<Cactus %r>' % self.name


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.Unicode(255))
    object_id = db.Column(db.Integer)
    object = generic_relationship(object_type, object_id)

    def __repr__(self):
        return '<Like %r>' % self.name


class RelatedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image = db.Column(db.Unicode(128), nullable=False)
    cactus_id = db.Column(db.Integer, db.ForeignKey('cactus.id'), nullable=False)

    def __repr__(self):
        return '<RelatedProduct %r>' % self.name


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=False)
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users',
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


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
    extra_js = ['/static/js/ckeditor.js', '/static/js/admin.js']

    def is_accessible(self):
        return (
            current_user.is_active
            and current_user.is_authenticated
            and current_user.has_role('superuser')
        )

    def _handle_view(self, name, **kwargs):
        print('wtf')
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for('security.login', next=request.url))

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
            url_relative_path='media/',
            thumbnail_size=(320, 320, True),
        )
    }

    form_overrides = {
        'description': CKTextAreaField,
    }


admin = Admin(app, name='cacti', base_template='my_master.html', template_mode='bootstrap4')
admin.add_view(CustomModelView(Cactus, db.session))
admin.add_view(CustomModelView(RelatedProduct, db.session))
admin.add_view(CustomModelView(User, db.session))
admin.add_view(CustomModelView(Role, db.session))


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


@app.route('/')
def index():
    difficulty = request.args.get('difficulty')

    if difficulty:
        cacti = Cactus.query.filter_by(difficulty=difficulty).all()
    else:
        cacti = Cactus.query.all()

    return render_template(
        'index.html',
        cacti=cacti,
        difficulty=Cactus.DIFFICULTY,
    )


@app.route('/route/<int:pk>')
def detail(pk):
    cactus = Cactus.query.filter_by(id=pk).first()
    if not cactus:
        raise NotFound
    return render_template('detail.html', cactus=cactus)


@app.route('/api/likes/cactus/<int:pk>')
def cactus_likes(pk):
    cactus = Cactus.query.filter_by(id=pk).first()
    likes = Like.query.filter_by(object=cactus).count()
    return jsonify({'likes': likes})


@app.route('/api/likes/cactus', methods=['POST'])
def create_cactus_likes():
    if request.method == 'POST':
        data = request.json
        pk = data.get('pk')
        cactus = Cactus.query.filter_by(id=pk).first()
        like = Like(object=cactus)
        db.session.add(like)
        db.session.commit()
        return jsonify({'detail': 'liked'})


# @app.route('/likes/product/<int:pk>')
# def detail(pk):
#     cactus = Cactus.query.filter_by(id=pk).first()
#     if not cactus:
#         raise NotFound
#     return jsonify()


# @app.route('/like/cactus', methods=['POST'])
# def user():
#     if request.method == 'POST':
#         data = request.form
#         print(data)


@app.before_first_request
def create_user():
    if not user_datastore.find_user(email="test@me.com"):
        user_datastore.create_user(email="test@me.com", password=hash_password("password"))
    db.session.commit()


if __name__ == '__main__':
    app.run()
