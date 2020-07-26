# -*- coding: utf-8 -*-

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, redirect, request, url_for, jsonify
from flask_wtf import FlaskForm
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from database import Database
from functions import authorization, get_user_courses, get_user_cmms, create_forms, give_out_forms, \
    create_cmm, delete_cmm, get_info_about_spreadsheet, get_folder_url, delete_forms, set_grades_in_coursework


db = Database(db='cmm_constructor', username='cmm_admin', host='localhost', port='5432', password='Atlirgsu0')
db.create_tables()
schedule = BackgroundScheduler(daemon=True)
schedule.add_job(set_grades_in_coursework, 'interval', seconds=30)
schedule.start()

class NameForm(FlaskForm):
    cmm_name = StringField('Название КИМа', validators=[DataRequired()])
    submit = SubmitField('ОК')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'houston-we-have-a-problem'
USER_EMAIL = "class@miem.hse.ru"
CORS(app, resources={r'/*': {'origins': '*'}})
api = Api(app)


@app.route('/cmm-name', methods=['GET', 'POST'])
def submit_cmm_name():
    response_object = {'status': 'success'}
    if request.method == 'POST':
        post_data = request.get_json()
        response_object['cmm_name'] = post_data.get('cmm_name')
        create_cmm(db, response_object['cmm_name'], USER_EMAIL)
        post_user_cmms()
    return jsonify(response_object)


@app.route('/user-courses', methods=['GET', 'POST'])
def post_user_courses():
    courses = get_user_courses(db, USER_EMAIL)
    response_object = {'courses': courses}
    return jsonify(response_object)


@app.route('/user-cmms', methods=['GET', 'POST'])
def post_user_cmms():
    cmms = get_user_cmms(db, USER_EMAIL)
    response_object = {'cmms': cmms}
    return jsonify(response_object)


@app.route('/user-courses/<cmm_id>', methods=['DELETE'])
def remove_cmm(cmm_id):
    response_object = {'status': 'success'}
    if request.method == 'DELETE':
        delete_cmm(cmm_id, USER_EMAIL)
        response_object['message'] = 'CMM removed!'
    return jsonify(response_object), 200

@app.route('/main', methods=['GET', 'POST'])
def main():
    authorization(db, USER_EMAIL)
    #courses = get_user_courses(USER_EMAIL)
    #cmms = get_user_cmms(USER_EMAIL)
    #data = {"courses": courses, "cmms": cmms}
    post_user_courses()
    post_user_cmms()

    """form = NameForm()
    if form.validate_on_submit():
        create_cmm(form.cmm_name.data, USER_EMAIL)
        print('create_cmm')
        return redirect(url_for('main'))"""

    #return render_template('main.html', data=data, form=form)
    return None


@app.route('/open_folder', methods=['GET', 'POST'])
def open_folder():
    spreadsheet_id = request.form['spreadsheetId']
    url = get_folder_url(spreadsheet_id, USER_EMAIL)
    return jsonify({"url": url})


@app.route('/delete_cmm', methods=['GET', 'POST'])
def delete_control_measuring_material():
    spreadsheet_id = request.form['spreadsheetId']
    delete_cmm(spreadsheet_id, USER_EMAIL)
    return redirect(url_for('main'))


@app.route('/get_information')
def get_information_about_cmm():
    spreadsheet_id = request.args.get('spreadsheet_id')
    spreadsheet_name = request.args.get('spreadsheet_name')
    spreadsheet_info = get_info_about_spreadsheet(spreadsheet_id)
    print(spreadsheet_info)

    return render_template('createVariant.html', spreadsheetInfo=spreadsheet_info, spreadsheetName=spreadsheet_name,
                           spreadsheetId=spreadsheet_id)


@app.route('/create_variants')
def create_variants():
    questions = request.args.get('questions').split(',')
    amount = request.args.get('amount')
    spreadsheet_id = request.args.get('spreadsheet_id')

    create_forms(questions, amount, spreadsheet_id)

    return redirect(url_for('main'))


@app.route('/get_course')
def get_course():
    spreadsheet_id = request.args.get('spreadsheet_id')
    courses = get_user_courses(db, USER_EMAIL)
    spreadsheet = db.search_for_spreadsheet(spreadsheet_url)
    spreadsheet_name = spreadsheet[0][1]
    folder_id = spreadsheet[0][4]

    return render_template('giveOutVariants.html', spreadsheetId=spreadsheet_id, courses=courses,
                           spreadsheetName=spreadsheet_name, folderId=folder_id)


@app.route('/give_out_variants')
def give_out_variants():
    course_name = request.args.get('course')
    task_name = request.args.get('task_name')
    folder_id = request.args.get('folder_id')
    start_date = request.args.get('start_date')
    start_time = request.args.get('start_time')
    end_date = request.args.get('end_date')
    end_time = request.args.get('end_time')

    give_out_forms(folder_id, course_name, task_name, start_date, start_time, end_date, end_time, USER_EMAIL)

    return redirect(url_for('main'))


@app.route('/delete_variants')
def delete_variants():
    spreadsheet_id = request.args.get('spreadsheet_id')
    delete_forms(spreadsheet_id)

    return redirect(url_for('main'))


@app.route('/get_cmms')
def get_cmms():
    cmms = get_user_cmms(db, USER_EMAIL)
    return jsonify(cmms)


if __name__ == '__main__':
    app.run(debug=True)
