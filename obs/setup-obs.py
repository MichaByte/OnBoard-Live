import obsws_python as obs
import os

# pass conn info if not in config.toml
client = obs.ReqClient(host='localhost', port=4455, password=os.environ["OBSWS_PASSWORD"])

scene = client.get_scene_list().scenes[0]['sceneName']

inputs = client.get_scene_item_list(name=scene).scene_items

print(client.get_input_default_settings("browser_source").default_input_settings)

if inputs == []:
    client.create_input(sceneName=scene, inputName="Browser", inputKind="browser_source", inputSettings={'css': 'body { margin: 0px auto; overflow: hidden; }', 'fps': 30, 'fps_custom': True, 'height': 1080, 'is_local_file': True, 'local_file': '/home/micha/index.html', 'reroute_audio': True, 'restart_when_active': False, 'shutdown': False, 'webpage_control_level': 0, 'width': 1920}, sceneItemEnabled=True)
