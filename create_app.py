import os
dirs = os.listdir('./apps/')
while True:
    print('Input folder name (в apps/): ',end='')
    folder_name = input()
    if folder_name in dirs:
        print('Such name in the directory apps/ already exists')
        continue
    break
print('Input name of class and file: ',end='')
class_name = input()
print('Input name of app (call this in the bot): ',end='')
app_name = input()
os.mkdir('./apps/'+folder_name)
open('./apps/'+folder_name+'/__init__.py', 'w').close()
with open('./templates/__main__.py.template', 'r', encoding='utf-8') as file:
    text = file.read()
    main_file = open('./apps/'+folder_name+'/__main__.py', 'w', encoding='utf-8')
    main_file.write(text)
    main_file.close()
with open('./templates/default_app_file.py.template', 'r', encoding='utf-8') as file:
    text = file.read()
    text = text.replace('__REPLACE_IT_2__', class_name.capitalize())
    app_file = open('./apps/'+folder_name+'/'+class_name+'.py', 'w', encoding='utf-8')
    app_file.write(text)
    app_file.close()
with open('./templates/config.template', 'r', encoding='utf-8') as file:
    text = file.read()
    text = text.replace('__REPLACE_IT_1__', app_name)
    app_file = open('./apps/'+folder_name+'/config', 'w', encoding='utf-8')
    app_file.write(text)
    app_file.close()
os.mkdir('./apps/'+folder_name+'/logs/')
print('App apps/'+folder_name+'/ was successfully created')
