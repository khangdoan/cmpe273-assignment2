from flask import Flask, escape, request, url_for, redirect, Response, jsonify, json
import sqlite3
from flask import g

DATABASE = './assignment2.db'
UPLOAD_FOLDER = 'files'

def getDB():
    db = getattr(g, '_database', None)
    if db is None: db = g._database = sqlite3.connect(DATABASE)
    return db


def queryDB(query, args=(), single=False):
    """used for quick and dirty sqlite extraction. NOT for insertion"""
    db = getDB()
    # db.row_factory = sqlite3.Row
    cursor = db.execute(query, args)
    out = cursor.fetchall()
    cursor.close()
    return (out[0] if out else None) if single else out


def getAnswerKey(id=0):
    out = queryDB("select answer_keys from test where id==(?)", id, single=True)
    return out


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def hello():
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!'

@app.teardown_appcontext
def closeDB(exception):
    db = getattr(g, '_database', None)
    if db: db.close()


@app.route('/api/tests', methods=['POST'])
def createTest():
    # select count(*) from test
    if request.method == 'POST':
        try:
            payload = request.get_json()
            answerKeys = payload['answer_keys']
            # print(f'{answerKeys}')
            buffer = ''
            subject = payload['subject']
            for keys in answerKeys:
                buffer = buffer + answerKeys[keys]
            id = int(queryDB('select count(*) as count from test', single=True)[0]) + 1
            with sqlite3.connect(DATABASE) as con:
                cursor = con.cursor()
                cursor.execute("INSERT INTO test (id,subject,answer_keys) VALUES (?,?,?)"
                               , (id, subject, buffer))
                con.commit()
        except:
            con.rollback()
            print('POST ERROR!')

        finally:
            con.close()
            return jsonify(
                test_id=id,
                subject=subject,
                answer_keys=answerKeys,
                submission=[]
            ), 201


@app.route('/api/tests/<int:scantron_id>/scantrons', methods=['POST'])
def uploadScantrons(scantron_id=0):
    if request.method == 'POST':
        import os
        retDict = {}
        try:
            # process file
            file = request.files.get('data')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            with app.open_resource(UPLOAD_FOLDER+'/'+file.filename) as f:
                payload = json.load(f)
            url = f'{request.host_url}{UPLOAD_FOLDER}/{file.filename}'
            answers = payload['answers']
            buffer = ''
            for i in answers:
                buffer = buffer + answers[i]

            scantron_score = 0
            answer_key = queryDB("select answer_keys from test where id = ?",[scantron_id],single=True)[0]
            for i in range(0,len(buffer)):
                if buffer[i] == answer_key[i]:
                    scantron_score = scantron_score +1
                retDict[str(i+1)] = {"actual": buffer[i], "expected": answer_key[i]}

            id = int(queryDB('select count(*) as count from scantron', single=True)[0]) + 1
            with sqlite3.connect(DATABASE) as con:
                cursor = con.cursor()
                cursor.execute(
                    "INSERT INTO scantron (id, scantron_url, name, subject, answers, test_id) VALUES (?,?,?,?,?,?)"
                    , (id, url, payload['name'], payload['subject'], buffer, scantron_id))
                con.commit()
        except:
            con.rollback()
        finally:
            con.close()
            return jsonify(
                scantron_id=id,
                scantron_url=url,
                name=payload['name'],
                subject=payload['subject'],
                score=scantron_score,
                result=retDict
            ), 201
    return "ERROR"


@app.route('/api/tests/<int:testID>',methods=['GET'])
def getResults(testID):
    if request.method == 'GET':
        answerKey = queryDB("select * from test where id = ?",[testID])[0]
        answers = queryDB("select * from scantron where test_id = ?",[testID])
        submissions =[]
        answerKeyDeser = {}
        for i in range(0,len(answerKey)):
            answerKeyDeser[str(i+1)] = answerKey[2][i]
        answer_off = 4
        for answer in answers:
            score = 0
            result = {}
            for i in range(0,len(answer[answer_off])):
                if answer[answer_off][i] == answerKey[2][i]:
                    score = score +1
                result[int(i+1)] = {"actual": answer[answer_off][i],
                                    "excepted": answerKey[2][i]}
            submissions.append(
                {"scantron_id":answer[0],"scantron_url":answer[1],
                        "name": answer[2], "subject":answer[3], "score":score,"result":result}
            )
        return jsonify(test_id=answerKey[0],subject=answerKey[1],answer_key=answerKeyDeser,submissions=submissions), 201


    return "todo"
