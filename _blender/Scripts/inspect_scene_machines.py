import re

with open('Assets/Scenes/AIGym.unity', 'r', encoding='utf-8') as f:
    text = f.read()

stations = re.findall(r'--- !u!114 &(\d+)\nMonoBehaviour:.*?m_EditorClassIdentifier: Assembly-CSharp::ExerciseStation.*?\n  machineName: "(.*?)"\n  useRange: ([^\n]+)\n  exitDistance: ([^\n]+)\n  pullSpeed: ([^\n]+)\n  pose:.*?\n  machineAnimState: ([^\n]+)\n  playerAnimState: ([^\n]+)', text, re.DOTALL)
print(f"Total ExerciseStations found: {len(stations)}")
for s in stations:
    name_unicode = s[1].encode('utf-8').decode('unicode_escape')
    print(f"ID={s[0]:12} | Name={name_unicode:25} | PlayerAnim={s[6]:15} | MachineAnim={s[5]}")

m = re.search(r'--- !u!4 &1990010008\nTransform:.*?m_Children:\n(.*?)(?=  m_Father:)', text, re.DOTALL)
if m:
    children = re.findall(r'- \{fileID: (\d+)\}', m.group(1))
    print(f"\nTotal children in 04_Equipment: {len(children)}")
    print("Children:", children)
