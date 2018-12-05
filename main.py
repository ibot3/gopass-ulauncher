from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from subprocess import check_output
from os import path
import re

PASSWORD_ICON = 'images/icon.png'
FOLDER_ICON = 'images/folder.png'
MORE_ICON = 'images/more.png'
WARNING_ICON = 'images/warning.png'
PASSWORD_DESCRIPTION = 'Enter to copy to the clipboard'
FOLDER_DESCRIPTION = 'Enter to navigate to'


class PassExtension(Extension):

    def __init__(self):
        super(PassExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

    def search(self, path_ext=None, pattern=None, depth=None):

        store_location = path.expanduser(self.preferences['store-location'])

        matches = []

        if not path_ext:
            path_ext = ''

        if not pattern:
            pattern = ''

        if depth:
            max_depth = '-maxdepth {} '.format(str(depth))
        else:
            max_depth = ''

        searching_path = path.join(store_location, path_ext)

        for t in ("d", "f"):
            cmd = 'find {} {}-type {} -not -path *.git -not -name .* -iname *{}*'.format(searching_path,
                                                                                         max_depth,
                                                                                         t,
                                                                                         pattern)
            items = re.findall("{0}/*(.+)".format(searching_path), check_output(cmd.split(" ")))
            items.sort()
            matches = matches + items

        print matches

        return matches


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        path_ext = ""

        query_arg = event.get_argument()

        if not query_arg:
            result = extension.search(depth=1)
        else:
            path_ext = path.split(query_arg)[0]
            pattern = path.split(query_arg)[1]

            if path_ext.startswith('/'):
                path_ext = path_ext[1:]

            if not query_arg.endswith('/'):
                result = extension.search(path_ext=path_ext, pattern=pattern)
            else:
                store_location = path.expanduser(extension.preferences['store-location'])

                if not path.exists(path.join(store_location, path_ext)):
                    return RenderResultListAction([ExtensionResultItem(icon=WARNING_ICON,
                                                                       name='Invalid path',
                                                                       description='Please check your arguments.',
                                                                       on_enter=DoNothingAction()
                                                                       )])
                else:
                    result = extension.search(path_ext=path_ext, pattern=pattern, depth=1)

        nb_results = int(extension.preferences["max-results"])

        for i in result[:nb_results]:

            if ".gpg" in i:
                # remove file extension
                i = i[:-4]

                icon = PASSWORD_ICON
                description = PASSWORD_DESCRIPTION
                action = RunScriptAction("pass -c {0}/{1}".format(path_ext, i), None)
            else:
                icon = FOLDER_ICON
                description = FOLDER_DESCRIPTION
                action = SetUserQueryAction("{0} {1}/".format(extension.preferences['pass-keyword'],
                                                              path.join(path_ext, i)))

            items.append(ExtensionResultItem(icon=icon,
                                             name="{0}".format(i),
                                             description=description,
                                             on_enter=action))

        if nb_results < len(result):
            items.append(ExtensionResultItem(icon=MORE_ICON,
                                             name='Keep typing...',
                                             description='More items are available.'
                                                         + ' Narrow your search by entering a pattern.',
                                             on_enter=DoNothingAction()))

        return RenderResultListAction(items)


if __name__ == '__main__':
    PassExtension().run()
