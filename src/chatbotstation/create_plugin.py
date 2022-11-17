import os, sys
while True:
    name = input('Input plugin name: ')
    dirs = os.listdir('./plugins/')
    name = name.capitalize()
    if name+'.py' in dirs:
        print('Such name in the directory plugins/ already exists')
        continue
    break
with open('./templates/default_plugin_file.py.template', 'r', encoding='utf-8') as file:
    text = file.read()
    text = text.replace('__REPLACE_ME__', name)
    plugin_file = open('./plugins/'+name+'.py', 'w', encoding='utf-8')
    plugin_file.write(text)
    plugin_file.close()
print('Plugin plugins/'+name+'.py was successfully created.')
