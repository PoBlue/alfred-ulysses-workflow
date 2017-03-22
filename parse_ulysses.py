import os
from os.path import join
import subprocess
import plistlib

# SHEET = "com.soulmen.ulysses3.sheet"
# GROUP = "com.soulmen.ulysses3.group"

ULYSSES3_LIB = join(os.environ['HOME'],'Library', 'Mobile Documents',
                    'X5AZV975AG~com~soulmen~ulysses3','Documents', 'Library')
GROUPS_ROOT = join(ULYSSES3_LIB, 'Groups-ulgroup')
UNFILED_ROOT = join(ULYSSES3_LIB, 'Unfiled-ulgroup')


MDFIND_SHEET_QUERY = '((** = "%s*"cdw) && (kMDItemKind = "Ulysses Sheet*"cdwt))'
MDFIND_GROUP_QUERY = '((** = "%s*"cdw) && (kMDItemKind = "Ulysses Group*"cdwt))'

class Node:  # consider abstract

    def __init__(self, dirpath, parent_group):
        self.dirpath = dirpath
        self.parent_group = parent_group
        self.title = None

    def get_ancestors(self):
        ancestors = []
        ancestor = self.parent_group
        while ancestor:
            ancestors.append(ancestor)
            ancestor = ancestor.parent_group
        ancestors.reverse()
        return ancestors

    def get_alfred_path_list(self):
        return [a.name for a in self.get_ancestors()]



class Group(Node):

    is_group = True
    if_sheet = False

    def __init__(self, dirpath, parent_group):
        Node.__init__(self, dirpath, parent_group)
        self.child_groups = []
        self.child_sheets = []
        self.openable_file = join(self.dirpath, 'Info.ulgroup')
        self.name = plistlib.readPlist(join(self.dirpath, 'Info.ulgroup'))['displayName']
        #self.name = self.name.decode('utf-8')
        self.title = self.name


class Sheet(Node):

    is_group = False
    is_sheet = True

    def __init__(self, dirpath, parent_group):
        Node.__init__(self, dirpath, parent_group)
        self.dirpath = dirpath
        self.openable_file = dirpath
        with open(join(self.dirpath, 'Text.txt'), 'r') as f:
            self.first_line = f.readline().decode('utf-8').strip()
        self.title = self.first_line


def filter_nodes_by_openable_file(nodes, openable_file_list):
    return [node for node in nodes if node.openable_file in openable_file_list]


def filter_groups(groups, query):
    openable_files = subprocess.check_output(
        ['mdfind', MDFIND_GROUP_QUERY % query]).split('\n')
    return filter_nodes_by_openable_file(groups, openable_files)


def filter_sheets(sheets, query):
    openable_files = subprocess.check_output(
        ['mdfind', MDFIND_SHEET_QUERY % query]).split('\n')
    return filter_nodes_by_openable_file(sheets, openable_files)



def create_tree(rootgroupdir, parent_group):
    '''recursively build group tree starting from rootgroupdir
    '''
    assert rootgroupdir.endswith('-ulgroup')
    filelist = os.listdir(rootgroupdir)
    assert 'Info.ulgroup' in filelist
    sheetdirlist = [p for p in filelist if p.endswith('.ulysses')]
    groupdirlist = [p for p in filelist if p.endswith('-ulgroup')]

    # Create group
    group = Group(rootgroupdir, parent_group)

    # Add Sheets
    for sheetdir in sheetdirlist:
        sheet = Sheet(join(rootgroupdir, sheetdir), group)
        group.child_sheets.append(sheet)

    # Recursively add groups
    for child_groupdir in groupdirlist:
        child_group = create_tree(join(rootgroupdir, child_groupdir), group)
        assert child_group != group
        group.child_groups.append(child_group)

    return group


def walk(root_group):
    '''groups, sheets = walk(root_group)
    '''
    groups = [root_group]
    sheets = list(root_group.child_sheets)
    for child_group in root_group.child_groups:
        descendent_groups, descendent_sheets = walk(child_group)
        groups += descendent_groups
        sheets += descendent_sheets
    return groups, sheets


def find_group_by_path(root_group, dirpath):
    groups, _ = walk(root_group)
    for group in groups:
        if group.dirpath == dirpath:
            return group
    #raise Exception('Group not found with dirpath == ' + dirpath)
