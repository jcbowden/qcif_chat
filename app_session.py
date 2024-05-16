from flask import Flask, render_template_string, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from pprint import pprint
import datetime

# Create the Flask application
app = Flask(__name__)

# Details on the Secret Key: https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY
# NOTE: The secret key is used to cryptographically-sign the cookies used for storing
#       the session data.
app.secret_key = 'ABC_SECRET_KEY'

client = MongoClient()

# To enable automatic update of messages, we can try to use changestream functionality, however, the DB needs to be run as a replical set (see qcif_chat_instructions.md)
# CHANGE_STREAM_DB='mongodb://172.30.143.25:5000'
# change_stream = client.changestream.collection.watch([{
    # '$match': {
        # 'operationType': { '$in': ['insert'] }
    # }
# }])

db=client.qcif_users

# storage = db.storage
usernames = db.usernames
messages = db.messages
#storage.drop()
#exit()


# was: database_new_entry
def database_new_chatuser(new_result):

            global usernames
            if usernames.find({'Name': new_result['chatuser'] }).count() > 0:
                  avaliability_flag=True
                  print('Trying to overwrite chatuser issue')
                  exit()

            user_details = {
                  'Name': new_result['chatuser'],
                  'User': new_result
            }
            
            entry_status = usernames.insert_one(user_details)
            return entry_status
            
# was: database_update_entry
def database_update_chatuser(key_val,new_result):
            global usernames
            entry_status = usernames.update_one(
                  {'Name':key_val},
                  {
                        "$set": {'User':new_result}
                  }
            )
            print('inside database_update_entry', key_val, new_result)
            return entry_status

            
def format_first_post(Sender, Receiver) :
    mssg_post = {
        "Sender": Sender,
        "Receiver": Receiver,
        "Read": False,
        "text": 'This is your first chat message with ' + Receiver,
        "date": datetime.datetime.now(tz=datetime.timezone.utc)
    } 
    
    return mssg_post
    
def format_message_post(Sender, Receiver, text) :
    new_post = {
        "Sender": Sender,
        "Receiver": Receiver,
        "Read": False,
        "text": text,
        "date": datetime.datetime.now(tz=datetime.timezone.utc)
    } 
    
    return new_post
    
    
data={}

@app.route('/')
def getuser():
   return redirect(url_for('createuser'))
   
   
# Adds the chatuser value to the Flask session and also adds the user to the
# database. There seems to be some technical debt here inherited from the 
# original example project
@app.route('/adduser', methods=['POST'])
def adduser():
    if request.method == 'POST':
        # Save the form data to the session object
        result = request.form
        print(result)
        print(result['chatuser'])
        session['chatuser'] = request.form['chatuser']
        global data

        if usernames.find({'Name': result['chatuser'] }).count() > 0:
            avaliability_flag=True
            # Queryresult = usernames.find_one({'Name': result['chatuser']})
            # pass_dict=Queryresult['User']
        else:
            avaliability_flag=False
        print('Check if key available: ',avaliability_flag)

        print('checking db existence')
        if avaliability_flag==False: #not (result['Name'] in data.keys()):
            data[result['chatuser'] ]=result
            print('data',data)
            print("result['chatuser']",data[result['chatuser']])
            entry_status=database_new_chatuser(result)
            # return render_template("chatwith.html",result = result)
            return redirect(url_for('chatwith'))
        else:
            return redirect(url_for('chatwith'))
        
    
@app.route('/createuser', methods=['GET', 'POST'])
def createuser():
    return render_template('createuser.html')


@app.route('/chatwith', methods=['GET', 'POST'])
def chatwith():
    print("Chat with list ===========")
    global data
    tl=['  User Name  ']
    global db
    coll1 = db.usernames #selecting the coll1 in myDatabase
    user_dict={}
    for document in coll1.find():
        print('database',document)
        print("split",document['Name'],document['User'])
        user_dict[document['Name']]=document['User']
    return render_template('chatwith.html',newuserdict=user_dict,headings=tl)
    
    
def get_sorted_messages(Sender, Receiver ):
    message_list=[]
    for document in messages.find({'Sender':Sender, 'Receiver': Receiver }):
        # print(type(document))
        message_list.append(document)
    for document in messages.find({'Sender': Receiver, 'Receiver': Sender  }):
        message_list.append(document)
    sorted_list = sorted(message_list, key=lambda d: d['date'], reverse=True)
    message_num = 1
    message_dict = {}
    for document in sorted_list:
        d = document['date'].strftime("%m/%d/%Y, %H:%M:%S")
        message_dict[message_num] = document['Sender'] + ': (' + d + ') ' +document['text']
        message_num = message_num + 1
    print('Number of messages to be printed: ',message_num)
    return message_dict

@app.route('/chatwithme/<string:iname>',methods = [ 'GET', 'POST'])
def chatwithme(iname):
    #name_var=data[iname]
    global messages
    if request.method == 'POST':
        # Save the form data to the session object
        result = request.form
        entry_status =  messages.insert_one(format_message_post(session['chatuser'] , iname, result['message'] ))
        print('insert_one entry_status: ', entry_status)
        message_dict = get_sorted_messages(session['chatuser'], iname ) 
        
        return render_template('chatwithmepage.html',sname=iname,  all_messages=message_dict)
    else:
        # Queryresult = messages.find_one({'Sender': session['chatuser'], 'Receiver': iname })
        # if Queryresult == None:
        #     messages.insert_one(format_first_post(session['chatuser'] , iname))
        message_dict = get_sorted_messages(session['chatuser'], iname )
        return render_template('chatwithmepage.html',sname=iname,  all_messages=message_dict)
        

      
@app.route('/logout_chat')
def logout_chat():
    # Clear the chatuser stored in the session object
    if 'chatuser' in session:
        chatuser = session['chatuser'] 
        session.pop('chatuser', default=None)
        retstring =  chatuser + '  session has been deleted!'
        print(retstring )
        return redirect(url_for('createuser'))
    else:
        print('No chatuser key found in session')
        return redirect(url_for('createuser'))


if __name__ == '__main__':
    app.run()