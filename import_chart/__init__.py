import json
import os

import easygui

from export_chart.batcher import batch_charts
from export_chart.packer import pack_to_omgz
from zip_unpacker import unpack_zip

from .converter import malody2omegar
from .dir_importer import import_dir


def main() -> None:
    mode = easygui.ynbox('请选择导入模式', '导入谱面', ('从 mc(z) 文件导入', '从文件夹导入'))
    if mode is None:
        return
    elif mode:
        chart_list = easygui.fileopenbox('选择文件（支持多选）', '导入谱面', '*.mcz', ['*.mcz', '*.mc'], multiple=True)
        if not chart_list:
            return

        ok_list = []
        not_ok_list = []
        info_list = {}
        for chart in chart_list:
            try:
                chart_dir, file_name = os.path.split(chart)
                chart_name, chart_ext = os.path.splitext(file_name)
                if chart_ext == '.mcz':
                    target = os.path.join(chart_dir, chart_name)
                    if os.path.isdir(target):
                        if not easygui.ynbox(f'文件夹 {target} 已存在，确认要覆盖吗？', '导入谱面', ('确认', '取消')):
                            raise Exception('已存在同名文件夹')
                    else:
                        os.makedirs(target)
                    unpack_zip(chart, target)
                    info_list[target] = import_dir(target)
                elif chart_ext == '.mc':
                    target = os.path.join(chart_dir, chart_name+'.omg')
                    if os.path.isfile(target) and not easygui.ynbox(f'文件 {target} 已存在，确认要覆盖吗？', '导入谱面', ('确认', '取消')):
                        raise Exception('已存在同名文件')
                    mc_data = json.load(open(chart, encoding='utf-8'))
                    project_data = malody2omegar(mc_data)[-1]
                    json.dump(project_data, open(target, 'w', encoding='utf-8'))
                else:
                    raise Exception('不支持的文件格式')
                ok_list.append(file_name)
            except Exception as e:
                not_ok_list.append(f'{file_name}:{repr(e)}')

        msg = f'{len(ok_list)} 个谱面导入成功'+'。；'[bool(ok_list)]
        for i in ok_list:
            msg += '\n'+i
        if not_ok_list:
            msg += f'\n{len(not_ok_list)} 个谱面导入失败：'
            for i in not_ok_list:
                msg += '\n'+i
        easygui.msgbox(msg, '导入谱面', '好的')

        if len(info_list) >= 1 and easygui.ynbox('是否要立即打包为 omgz 文件？', '导入谱面', ('好的', '不用了')):
            ok_list = []
            not_ok_list = []
            for dir_path, song_info in info_list.items():
                try:
                    files = batch_charts(**song_info)
                    pack_to_omgz(files, dir_path+'.omgz')
                    ok_list.append(dir_path)
                except Exception as e:
                    not_ok_list.append(f'{dir_path}:{repr(e)}')

            msg = f'{len(ok_list)} 个谱面已打包为 omgz'+'。；'[bool(ok_list)]
            for i in ok_list:
                msg += '\n'+i
            if not_ok_list:
                msg += f'\n{len(not_ok_list)} 个谱面打包失败：'
                for i in not_ok_list:
                    msg += '\n'+i
            easygui.msgbox(msg, '导入谱面', '好的')

    else:
        chart_dir = easygui.diropenbox('选择文件夹', '导入谱面')
        if chart_dir is None:
            return
        song_info = import_dir(chart_dir)
        easygui.msgbox('导入成功！', '导入谱面', '好的')
        if easygui.ynbox('是否要立即打包为 omgz 文件？', '导入谱面', ('好的', '不用了')):
            files = batch_charts(**song_info)
            pack_to_omgz(files, chart_dir+'.omgz')
            easygui.msgbox('成功打包为 omgz 文件！', '导入谱面', '好的')
