from flask import Flask, jsonify, g, request
from flask_cors import CORS

from sqlnet.lib.dbengine import DBEngine
import sys

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
CORS(app)

ctx = app.app_context()
ctx.push()

reload(sys)
sys.setdefaultencoding('utf8')

TEST_DB = 'data/test.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        g._engine = DBEngine(TEST_DB)
        db = g._database = g._engine.db
        g._table_names = db.get_table_names()
    return db

def read_data():
    question_list = getattr(g, '_question_list', None)
    sql_gt = getattr(g, '_sql_gt', None)
    sql_pred = getattr(g, '_sql_pred', None)
    if question_list is None:
        question_list = []
        sql_gt = []
        sql_pred = []

        with open('test2.log','r') as file:
            for line in file:
                line = line.strip()
                if(line.find('question:') != -1):
                    question_list.append(line[10:])
                elif(line.find('sql_gt:') != -1):
                    sql_temp = next(file)
                    if sql_temp.find('WHERE') != -1:
                        sql_gt_map = next(file)
                        sql_gt_map = eval(sql_gt_map)
                        
                        for key, value in sql_gt_map.iteritems():
                            key = ':' + key
                            if type(value) == int or type(value) == float:
                                value = str(value)
                            else:
                                value = "\'" + value + "\'"
                            sql_temp = sql_temp.replace(key, value)
                    sql_gt.append(sql_temp)
                    
                elif(line.find('sql_pred:') != -1):
                    sql_temp = next(file)
                    if sql_temp.find('WHERE') != -1:
                        sql_pred_map = next(file)
                        sql_pred_map = sql_pred_map.replace(': nan', ": u'nan'")
                        sql_pred_map = eval(sql_pred_map)
                        
                        for key, value in sql_pred_map.iteritems():
                            key = ':' + key
                            if type(value) == int or type(value) == float:
                                value = str(value)
                            else:
                                value = "\'" + value + "\'"
                            sql_temp = sql_temp.replace(key, value)
                    sql_pred.append(sql_temp)

        g._question_list = question_list
        g._sql_gt = sql_gt
        g._sql_pred = sql_pred

    return question_list, sql_gt, sql_pred

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/get_data', methods=['GET'])
def get_data():
    response_object = {}
    question_list, sql_gt, sql_pred = read_data()
    response_object['question_list'] = question_list
    response_object['sql_gt'] = sql_gt
    response_object['sql_pred'] = sql_pred
    return jsonify(response_object)

@app.route('/get_table_names', methods=['GET'])
def get_table_names():
    db = get_db()
    return jsonify(g._table_names)

@app.route('/get_table', methods=['POST'])
def get_table():
    response_object = {}
    if request.method == 'POST':
        post_data = request.get_json()
        table_name = post_data['val']
        rows = get_db().query('select * from %s'%table_name)
        response_object = rows.export('json')
    return jsonify(response_object)

@app.route('/query_db', methods=['POST'])
def query_db():
    response_object = {}
    if request.method == 'POST':
        post_data = request.get_json()
        query = post_data['query']

        rows = get_db().query(query)
        response_object = rows.export('json')
    return jsonify(response_object)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0')
