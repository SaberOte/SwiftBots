import os, sys
while True:
    print('Input file name: ',end='')
    file_name = input()
    dirs = os.listdir('./plugins/')
    if not file_name.endswith('.py'):
        file_name += '.py'
    if file_name in dirs:
        print('Such name in the directory plugins/ already exists')
        continue
    break
print('Input class name: ',end='')
class_name = input()
with open('./templates/default_plugin_file.py.template', 'r', encoding='utf-8') as file:
    text = file.read()
    text = text.replace('__REPLACE_ME__', class_name.capitalize())
    plugin_file = open('./plugins/'+file_name+'.py', 'w', encoding='utf-8')
    plugin_file.write(text)
    plugin_file.close()
print('Plugin plugins/'+file_name+'.py was successfully created.')
