from flask import Flask, render_template, flash, request, send_from_directory
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, FileField
import mysql.connector
import boto3
import os

from config import *

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

try:
    db = mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        passwd = DB_USERPASSWORD,
        database = DB_NAME,
        connection_timeout = 5
    )
    cursor = db.cursor()
except Exception as e: print(e)

class SignupForm(Form):
    name = TextField('Name:', validators=[validators.InputRequired()])
    email = TextField('Email:', validators=[validators.InputRequired(), validators.Length(min=6, max=35)])
    password = TextField('Password:', validators=[validators.InputRequired(), validators.Length(min=3, max=35)])
    photo = FileField('photo')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
            'favicon.ico',mimetype='image/vnd.microsoft.icon')

    @app.route("/admin", methods=['GET'])
    def admin():
        sql = 'SELECT * FROM users'
        cursor.execute(sql)
        results = cursor.fetchall()
        user_list = []
        for result in results:
            item = list(result)
            if item[4] == None:
                item.pop(4)
            else:
                location = boto3.client('s3').get_bucket_location(Bucket=S3_BUCKET)['LocationConstraint']
                item[4] = "https://s3-%s.amazonaws.com/%s/%s" % (location, S3_BUCKET, item[4])

                # s3_client = boto3.client('s3')
                # item[4] = s3_client.generate_presigned_url('get_object',
                #     Params={'Bucket': S3_BUCKET,'Key': item[4]}, ExpiresIn=300)

            user_list.append(item)
        return render_template('admin.html', users=user_list)

    @app.route("/", methods=['GET', 'POST'])
    def form():
        form = SignupForm(request.form)

        if request.method == 'POST':
            name = request.form['name']
            password = request.form['password']
            email = request.form['email']
            photo = request.files['photo']

            if form.validate():
            # Save the comment here.
                form.save(request)
                flash('Thanks for registration ' + name)

            else:
                flash('Error: All the form fields are required. ')

        return render_template('form.html', form=form)

    def save(self, request):

        sql = ''
        val = ''

        if request.files['photo']:
            s3 = boto3.client('s3')
            s3.upload_fileobj(request.files['photo'], S3_BUCKET, request.files['photo'].filename)
            sql = 'INSERT INTO users (name, password, email, attachment) VALUES (%s, %s, %s, %s)'
            val = (request.form['name'], request.form['password'], request.form['email'], request.files['photo'].filename)

        else:
            sql = 'INSERT INTO users (name, password, email) VALUES (%s, %s, %s)'
            val = (request.form['name'], request.form['password'], request.form['email'])

        cursor.execute(sql, val)
        db.commit()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
