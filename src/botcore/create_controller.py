import os, sys
while True:
    name = input('Input controller name: ')
    dirs = os.listdir('./controllers/')
    name = name.capitalize()
    if name+'.py' in dirs:
        print('Such name in the directory controllers/ already exists')
        continue
    break
with open('./templates/default_controller_file.py.template', 'r', encoding='utf-8') as file:
    text = file.read()
    text = text.replace('__REPLACE_ME__', name)
    controller_file = open('./controllers/'+name+'.py', 'w', encoding='utf-8')
    controller_file.write(text)
    controller_file.close()
print('Controller controllers/'+name+'.py was successfully created.')
