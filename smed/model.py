#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

from qt import *
import codecs

from xmlutil import *
from enums import *
import edit


class Node(QListViewItem):
    img_path = "/usr/share/icons/Tulliana-1.0/16x16/apps/"
    images = [
        img_path + "mycomputer.png",
        img_path + "kwikdisk.png",
        img_path + "kuser.png",
        img_path + "kservices.png",
        img_path + "remote.png"
    ]
    
    def last_item(self, parent):
        f = parent.firstChild()
        if f:
            while 1:
                if f.nextSibling():
                    f = f.nextSibling()
                else:
                    break
        return f
    
    def __init__(self, parent, type, name, data=None):
        f = self.last_item(parent)
        if f:
            QListViewItem.__init__(self, parent, f, name)
        else:
            QListViewItem.__init__(self, parent, name)
        self.mypix = QPixmap(self.images[type])
        self.setPixmap(0, self.mypix)
        self.nodeParent = parent
        self.nodeType = type
        self.nodeName = name
        self.nodeDesc = ""
        self.nodeProfile = NONE
        self.nodeArguments = []
        
        if data is not None:
            self.nodeDesc = getNodeText(data, "description", "")
            
            tmp = data.getAttribute("profile")
            if tmp == "global":
                self.nodeProfile = GLOBAL
            elif tmp == "package":
                self.nodeProfile = PACKAGE
            elif tmp == "":
                pass
            else:
                print "Method '%s' has unknown profile mode '%s'." % (self.nodeName, tmp)
            
            for item in getTagsByName(data, "instance"):
                self.nodeArguments.append((item.firstChild.data, True))

            for item in getTagsByName(data, "argument"):
                self.nodeArguments.append((item.firstChild.data, False))

        self.setOpen(True)
    
    def text(self, column):
        if self.__dict__.has_key("nodeName"):
            return self.nodeName
        else:
            return ""


class Model(QHBox):
    def __init__(self, *args):
        QHBox.__init__(self, *args)
        vb = QVBox(self)
        vb.layout().setMargin(2)
        vb.layout().setSpacing(2)
        self.list = QListView(vb)
        list = self.list
        list.setRootIsDecorated(True)
        list.addColumn("System Model")
        list.setSorting(-1)
        self.connect(list, SIGNAL("selectionChanged()"), self._change)
        hb = QHButtonGroup(vb)
        self.bt_group = QPushButton(QIconSet(QPixmap(Node.images[GROUP])), "", hb)
        QToolTip.add(self.bt_group, "Add group")
        self.connect(self.bt_group, SIGNAL("clicked()"), self._add_group)
        self.bt_class = QPushButton(QIconSet(QPixmap(Node.images[CLASS])), "", hb)
        QToolTip.add(self.bt_class, "Add class")
        self.connect(self.bt_class, SIGNAL("clicked()"), self._add_class)
        self.bt_method = QPushButton(QIconSet(QPixmap(Node.images[METHOD])), "", hb)
        QToolTip.add(self.bt_method, "Add method")
        self.connect(self.bt_method, SIGNAL("clicked()"), self._add_method)
        self.bt_notify = QPushButton(QIconSet(QPixmap(Node.images[NOTIFY])), "", hb)
        QToolTip.add(self.bt_notify, "Add notify")
        self.connect(self.bt_notify, SIGNAL("clicked()"), self._add_notify)
        self.bt_remove = QPushButton("X", hb)
        QToolTip.add(self.bt_remove, "Remove node")
        self.connect(self.bt_remove, SIGNAL("clicked()"), self._remove)
        self.editor = edit.NodeEdit(self)
        self.clear()
    
    def _change(self):
        item = self.list.selectedItem()
        if item is not None:
            self.editor.use_node(item)
    
    def _add_group(self):
        Node(self.list_top, GROUP, "(new_group)")
    
    def _add_class(self):
        item = self.list.selectedItem()
        if item == None:
            return
        if item.parent() != self.list_top:
            return
        Node(item, CLASS, "(new_class)")
    
    def _add_method(self):
        item = self.list.selectedItem()
        if item == None:
            return
        if (item.parent() is None) or (item.parent().parent() != self.list_top):
            return
        Node(item, METHOD, "(new_method)")
    
    def _add_notify(self):
        item = self.list.selectedItem()
        if item == None:
            return
        if (item.parent() is None) or (item.parent().parent() != self.list_top):
            return
        Node(item, NOTIFY, "(new_notify)")
    
    def _remove(self):
        item = self.list.selectedItem()
        if item:
            item.parent().takeItem(item)
            del item
    
    def clear(self):
        self.list.clear()
        self.list_top = Node(self.list, MODEL, "Model")
        self.editor.use_node(self.list_top)
    
    def open_as(self, model_file):
        self.clear()
        doc = parseDocument(model_file, "comarModel")
        
        for group in getTagsByName(doc.documentElement, "group"):
            groupItem = Node(self.list_top, GROUP, group.getAttribute("name"), group)
            for class_ in getTagsByName(group, "class"):
                classItem = Node(groupItem, CLASS, class_.getAttribute("name"), class_)
                for method in getTagsByName(class_, "method"):
                    Node(classItem, METHOD, method.getAttribute("name"), method)
                for method in getTagsByName(class_, "notify"):
                    Node(classItem, NOTIFY, method.getAttribute("name"), method)
        
        doc.unlink()
        self.fileName = model_file
    
    def _save(self, model_file):
        doc = newDocument("comarModel")
        addText(doc, doc.documentElement, "\n\n\n")
        g = self.list_top.firstChild()
        while g:
            ge = addNode(doc, doc, "group")
            ge.setAttribute("name", g.nodeName)
            addText(doc, ge, "\n")
            c = g.firstChild()
            while c:
                ce = addNode(doc, ge, "class")
                ce.setAttribute("name", c.nodeName)
                addText(doc, ce, "\n")
                m = c.firstChild()
                while m:
                    if m.nodeType == METHOD:
                        me = addNode(doc, ce, "method")
                        if m.nodeProfile != NONE:
                            if m.nodeProfile == GLOBAL:
                                me.setAttribute("profile", "global")
                            elif m.nodeProfile == PACKAGE:
                                me.setAttribute("profile", "package")
                        
                        for arg in m.nodeArguments:
                            addText(doc, me, "\n")
                            if arg[1]:
                                addTextNode(doc, me, "instance", unicode(arg[0]))
                            else:
                                addTextNode(doc, me, "argument", unicode(arg[0]))
                        
                    else:
                        me = addNode(doc, ce, "notify")
                    me.setAttribute("name", m.nodeName)
                    if m.nodeDesc:
                        addText(doc, me, "\n")
                        addTextNode(doc, me, "description", m.nodeDesc)
                        addText(doc, me, "\n")
                    m = m.nextSibling()
                    addText(doc, ce, "\n")
                c = c.nextSibling()
                addText(doc, ge, "\n")
            g = g.nextSibling()
            addText(doc, doc.documentElement, "\n\n\n")
        f = codecs.open(model_file, 'w', "utf-8")
        f.write(doc.toxml())
        f.close()
        doc.unlink()
    
    def open(self):
        name = QFileDialog.getOpenFileName(".", "Model Files (*.xml)", self, "lala", "Choose model file to open")
        if not name:
            return
        name = unicode(name)
        self.open_as(name)
    
    def save_as(self):
        name = QFileDialog.getSaveFileName(".", "Model Files (*.xml)", self, "lala", "Choose model file to save")
        if not name:
            return
        name = unicode(name)
        self._save(name)
        self.fileName = name
    
    def save(self):
        if self.fileName:
            self._save(self.fileName)
        else:
            self.save_as()
