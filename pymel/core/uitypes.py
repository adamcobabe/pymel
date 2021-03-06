import sys, re
import pymel.util as _util
import pymel.internal.pmcmds as cmds
import pymel.internal.factories as _factories
import pymel.internal as _internal
import pymel.versions as _versions
import maya.mel as _mm
_logger = _internal.getLogger(__name__)

def _resolveUIFunc(name):
    if isinstance(name, basestring):
        import windows
        try:
            return getattr(windows,name)
        except AttributeError:
            try:
                cls = getattr(dynModule,name)
                return cls.__melcmd__()
            except (KeyError, AttributeError):
                pass
    else:
        import inspect
        if inspect.isfunction(name):
            return name
        elif inspect.isclass(name) and issubclass(name, PyUI):
            name.__melcmd__()

    raise ValueError, "%r is not a known ui type" % name

if _versions.current() >= _versions.v2011:

    def toQtObject(mayaName):
        """
        Given the name of a Maya UI element of any type, return the corresponding QWidget or QAction. 
        If the object does not exist, returns None
        
        When using this function you don't need to specify whether UI type is a control, layout, 
        window, or menuItem, the first match -- in that order -- will be returned. If you have the full path to a UI object
        this should always be correct, however, if you only have the short name of the UI object,
        consider using one of the more specific variants: `toQtControl`, `toQtLayout`, `toQtWindow`, or `toQtMenuItem`.
        
        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findControl(mayaName)
        if ptr is None:
            ptr = mui.MQtUtil.findLayout(mayaName)
            if ptr is None:
                ptr = mui.MQtUtil.findMenuItem(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtcore.QObject)
        
    def toQtControl(mayaName):
        """
        Given the name of a May UI control, return the corresponding QWidget. 
        If the object does not exist, returns None
        
        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findControl(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QWidget)
        
    def toQtLayout(mayaName):
        """
        Given the name of a May UI control, return the corresponding QWidget. 
        If the object does not exist, returns None
        
        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findLayout(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QWidget)
    
    def toQtWindow(mayaName):
        """
        Given the name of a May UI control, return the corresponding QWidget. 
        If the object does not exist, returns None
        
        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findWindow(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QWidget)
        
    def toQtMenuItem(mayaName):
        """
        Given the name of a May UI menuItem, return the corresponding QAction. 
        If the object does not exist, returns None
        
        This only works for menu items. for Menus, use toQtControl or toQtObject
        
        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findMenuItem(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QAction)
        
class PyUI(unicode):
    def __new__(cls, name=None, create=False, **kwargs):
        """
        Provides the ability to create the PyUI Element when creating a class::

            import pymel.core as pm
            n = pm.Window("myWindow",create=True)
            n.__repr__()
            # Result: Window('myWindow')
        """

        if cls is PyUI:
            try:
                uiType = cmds.objectTypeUI(name)
                uiType = _uiTypesToCommands.get(uiType, uiType)
            except RuntimeError:
                try:
                    # some ui types (radioCollections) can only be identified with their shortname
                    uiType = cmds.objectTypeUI(name.split('|')[-1])
                    uiType = _uiTypesToCommands.get(uiType, uiType)
                except RuntimeError:
                    # we cannot query the type of rowGroupLayout children: check common types for these
                    uiType = None
                    for control in 'checkBox floatField button floatSlider intSlider ' \
                            'floatField textField intField optionMenu radioButton'.split():
                        if getattr(cmds, control)( name, ex=1, q=1):
                            uiType = control
                            break
                    if not uiType:
                        uiType = 'PyUI'
            try:
                newcls = getattr(dynModule, _util.capitalize(uiType) )
            except AttributeError:
                newcls = PyUI
                # objectTypeUI for panels seems to return weird results -
                # ie, TmodelPane ... check for them this way.
                # Other types should be detected correctly by objectTypeUI,
                # but this just provides a failsafe...
                for testType in 'panel scriptedPanel window control layout menu'.split():
                    if getattr(cmds, testType)( name, ex=1, q=1):
                        newcls = getattr(dynModule, _util.capitalize(testType),
                                         PyUI )
                        if newcls != PyUI:
                            break
        else:
            newcls = cls

        if not newcls is PyUI:
            if cls._isBeingCreated(name, create, kwargs):
                name = newcls.__melcmd__(name, **kwargs)
                _logger.debug("PyUI: created... %s" % name)
            else:
                # find the long name
                if '|' not in name and not issubclass(newcls,
                                                (Window,
                                                 Panel,
                                                 dynModule.ScriptedPanel,
                                                 dynModule.RadioCollection,
                                                 dynModule.ToolCollection)):
                    import windows
                    try:
                        if issubclass(newcls,Layout):
                            parent = windows.layout(name, q=1, p=1)
                        elif issubclass(newcls,Menu):
                            parent = windows.menu(name, q=1, p=1)
                        else:
                            parent = windows.control(name, q=1, p=1)
                        if parent:
                            name = parent + '|' + name

                    except RuntimeError:
                        # editors don't have a long name, so we keep the short name
                        if name not in cmds.lsUI( long=True,editors=True):
                            raise


        # correct for optionMenu
        if newcls == PopupMenu and cmds.optionMenu( name, ex=1 ):
            newcls = OptionMenu
        return unicode.__new__(newcls,name)

    @staticmethod
    def _isBeingCreated( name, create, kwargs):
        """
        create a new node when any of these conditions occur:
           name is None
           create is True
           parent flag is set
        """
        return not name or create or ( 'q' not in kwargs and kwargs.get('parent', kwargs.get('p', None)) )

    def __repr__(self):
        return u"ui.%s('%s')" % (self.__class__.__name__, self)
    def parent(self):
        buf = unicode(self).split('|')[:-1]
        if len(buf)==2 and buf[0] == buf[1] and _versions.current() < _versions.v2011:
            # pre-2011, windows with menus can have a strange name:
            # ex.  window1|window1|menu1
            buf = buf[:1]
        return PyUI( '|'.join(buf) )
    getParent = parent

    def type(self):
        try:
            return cmds.objectTypeUI(self)
        except:
            return None

    def shortName(self):
        return unicode(self).split('|')[-1]
    def name(self):
        return unicode(self)
    def window(self):
        return Window( self.name().split('|')[0] )

    delete = _factories.functionFactory( 'deleteUI', rename='delete' )
    rename = _factories.functionFactory( 'renameUI', rename='rename' )
    type = _factories.functionFactory( 'objectTypeUI', rename='type' )

    @classmethod
    def exists(cls, name):
        return cls.__melcmd__( name, exists=True )

    if _versions.current() >= _versions.v2011:
        asQtObject = toQtControl
        
class Panel(PyUI):
    """pymel panel class"""
    __metaclass__ = _factories.MetaMayaUIWrapper
    # note that we're not actually customizing anything, but
    # we're declaring it here because other classes will have this
    # as their base class, so we need to make sure it exists first

class Layout(PyUI):
    def __enter__(self):
        self.makeDefault()
        return self

    def __exit__(self, type, value, traceback):
        self.pop()

    def children(self):
        #return [ PyUI( self.name() + '|' + x) for x in self.__melcmd__(self, q=1, childArray=1) ]
        kids = cmds.layout(self, q=1, childArray=1)
        if kids:
            return [ PyUI( self.name() + '|' + x) for x in kids ]
        return []

    getChildren = children

    def walkChildren(self):
        for child in self.children():
            yield child
            if hasattr(child, 'walkChildren'):
                for subChild in child.walkChildren():
                    yield subChild

    def addChild(self, uiType, name=None, **kwargs):
        if isinstance(uiType, basestring):
            uiType = getattr(dynModule, uiType)
        assert hasattr(uiType, '__call__'), 'argument uiType must be the name of a known ui type, a UI subclass, or a callable object'
        args = []
        if name:
            args.append(name)
        if kwargs:
            if 'parent' in kwargs or 'p' in kwargs:
                _logger.warn('parent flag is set by addChild automatically. passed value will be ignored' )
                kwargs.pop('parent', None)
                kwargs.pop('p', None)
        kwargs['parent'] = self
        res = uiType(*args, **kwargs)
        if not isinstance(res, PyUI):
            res = PyUI(res)
        return res

    def makeDefault(self):
        """
        set this layout as the default parent
        """
        cmds.setParent(self)

    def pop(self):
        """
        set the default parent to the parent of this layout
        """
        p = self.parent()
        cmds.setParent(p)
        return p

    def clear(self):
        children = self.getChildArray()
        if children:
            for child in self.getChildArray():
                cmds.deleteUI(child)
    
    if _versions.current() >= _versions.v2011:
        asQtObject = toQtLayout
        
# customized ui classes
class Window(Layout):
    """pymel window class"""
    __metaclass__ = _factories.MetaMayaUIWrapper

#    if _versions.current() < _versions.v2011:
#        # don't set
#        def __enter__(self):
#            return self

    def __exit__(self, type, value, traceback):
        self.show()

    def show(self):
        cmds.showWindow(self)

    def delete(self):
        cmds.deleteUI(self, window=True)

    def layout(self):
        name = self.name()
        for layout in sorted(cmds.lsUI(long=True, controlLayouts=True)):
            # since we are sorted, shorter will be first, and the first layout we come across will be the base layout
            if layout.startswith(name):
                return PyUI(layout)

#            # create a child and then delete it to get the layout
#            res = self.addChild(cmds.columnLayout)
#            layout = res.parent()
#            res.delete()
#            return layout

    def children(self):
        res = self.layout()
        return [res] if res else []

    getChildren = children

    def window(self):
        return self

    def parent(self):
        return None
    getParent = parent

    if _versions.current() >= _versions.v2011:
        asQtObject = toQtWindow
    
class FormLayout(Layout):
    __metaclass__ = _factories.MetaMayaUIWrapper

    def __new__(cls, name=None, **kwargs):
        if kwargs:
            [kwargs.pop(k, None) for k in ['orientation', 'ratios', 'reversed', 'spacing']]

        self = Layout.__new__(cls, name, **kwargs)
        return self


    def __init__(self, name=None, orientation='vertical', spacing=2, reversed=False, ratios=None, **kwargs):
        """
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
        Layout.__init__(self, **kwargs)
        self._spacing = spacing
        self._orientation = self.Orientation.getIndex(orientation)
        self._reversed = reversed
        self._ratios = ratios and list(ratios) or []

    def attachForm(self, *args):
        kwargs = {'edit':True}
        kwargs['attachForm'] = [args]
        cmds.formLayout(self,**kwargs)

    def attachControl(self, *args):
        kwargs = {'edit':True}
        kwargs['attachControl'] = [args]
        cmds.formLayout(self,**kwargs)

    def attachNone(self, *args):
        kwargs = {'edit':True}
        kwargs['attachNone'] = [args]
        cmds.formLayout(self,**kwargs)

    def attachPosition(self, *args):
        kwargs = {'edit':True}
        kwargs['attachPosition'] = [args]
        cmds.formLayout(self,**kwargs)

    HORIZONTAL = 0
    VERTICAL = 1
    Orientation = _util.enum.Enum( 'Orientation', ['horizontal', 'vertical'] )

    def flip(self):
        """Flip the orientation of the layout """
        self._orientation = 1-self._orientation
        self.redistribute(*self._ratios)

    def reverse(self):
        """Reverse the children order """
        self._reversed = not self._reversed
        self._ratios.reverse()
        self.redistribute(*self._ratios)

    def reset(self):
        self._ratios = []
        self._reversed = False
        self.redistribute()


    def redistribute(self,*ratios):
        """
        Redistribute the child controls based on the ratios.
        If not ratios are given (or not enough), 1 will be used
        """

        sides = [["top","bottom"],["left","right"]]

        children = self.getChildArray()
        if not children:
            return
        if self._reversed:
            children.reverse()

        ratios = list(ratios) or self._ratios or []
        ratios += [1]*(len(children)-len(ratios))
        self._ratios = ratios
        total = sum(ratios)

        for i, child in enumerate(children):
            for side in sides[self._orientation]:
                self.attachForm(child,side,self._spacing)

            if i==0:
                self.attachForm(child,
                    sides[1-self._orientation][0],
                    self._spacing)
            else:
                self.attachControl(child,
                    sides[1-self._orientation][0],
                    self._spacing,
                    children[i-1])

            if ratios[i]:
                self.attachPosition(children[i],
                    sides[1-self._orientation][1],
                    self._spacing,
                    float(sum(ratios[:i+1]))/float(total)*100)
            else:
                self.attachNone(children[i],
                    sides[1-self._orientation][1])

    def vDistribute(self,*ratios):
        self._orientation = int(self.Orientation.vertical)
        self.redistribute(*ratios)

    def hDistribute(self,*ratios):
        self._orientation = int(self.Orientation.horizontal)
        self.redistribute(*ratios)

class AutoLayout(FormLayout):
    """
    AutoLayout behaves exactly like `FormLayout`, but will call redistribute automatically
    at the end of a 'with' statement block
    """
    def __exit__(self, type, value, traceback):
        self.redistribute()
        self.pop()

class TextScrollList(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    def extend( self, appendList ):
        """ append a list of strings"""

        for x in appendList:
            self.append(x)

    def selectIndexedItems( self, selectList ):
        """select a list of indices"""
        for x in selectList:
            self.selectIndexedItem(x)

    def removeIndexedItems( self, removeList ):
        """remove a list of indices"""
        for x in removeList:
            self.removeIndexedItem(x)

    def selectAll(self):
        """select all items"""
        numberOfItems = self.getNumberOfItems()
        self.selectIndexedItems(range(1,numberOfItems+1))

class PopupMenu(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    def __enter__(self):
        cmds.setParent(self,menu=True)
        return self

    def __exit__(self, type, value, traceback):
        p = self.parent()
        #Ensure we set the parent back to a layout not some ui element
        # like say a button which does not accept children
        if not cmds.layout(p, exists=True):
            p = p.parent()
        
        #However we want to be careful not to attach to a rowGroupLayout(textFieldButtonGrp etc)
        # in this case set the parent to the rowGroupLayout's parent
        if cmds.objectTypeUI(p) == u'rowGroupLayout':
            p = p.parent()
        cmds.setParent(p)
        return p

class OptionMenu(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    def __enter__(self):
        cmds.setParent(self,menu=True)
        return self

    def __exit__(self, type, value, traceback):
        p = self.parent()
        cmds.setParent(p)
        return p

    def addMenuItems( self, items, title=None):
        """ Add the specified item list to the OptionMenu, with an optional 'title' item """
        if title:
            cmds.menuItem(l=title, en=0, parent=self)
        for item in items:
            cmds.menuItem(l=item, parent=self)

    def clear(self):
        """ Clear all menu items from this OptionMenu """
        for t in self.getItemListLong() or []:
            cmds.deleteUI(t)
    addItems = addMenuItems

class Menu(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    def __enter__(self):
        cmds.setParent(self,menu=True)
        return self

    def __exit__(self, type, value, traceback):
        p = self.parent()
        #Ensure we set the parent back to a layout not some ui element
        # like say a button which does not accept children
        if not cmds.layout(p, exists=True):
            p = p.parent()
            
        #However we want to be careful not to attach to a rowGroupLayout(textFieldButtonGrp etc)
        # in this case set the parent to the rowGroupLayout's parent
        if cmds.objectTypeUI(p) == u'rowGroupLayout':
            p = p.parent()
        cmds.setParent(p)
        return p

    def getItemArray(self):
        """ Modified to return pymel instances """
        children = cmds.menu(self,query=True,itemArray=True)
        if children:
            return [MenuItem(item) for item in cmds.menu(self,query=True,itemArray=True)]
        else:
            return []

class SubMenuItem(Menu):
    def __enter__(self):
        cmds.setParent(self,menu=True)
        return self

    def __exit__(self, type, value, traceback):
        p = self.parent()
        cmds.setParent(p,menu=True)
        return p

    def getBoldFont(self):
        return cmds.menuItem(self,query=True,boldFont=True)

    def getItalicized(self):
        return cmds.menuItem(self,query=True,italicized=True)
    
    if _versions.current() >= _versions.v2011:
        asQtObject = toQtMenuItem
        
class CommandMenuItem(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    __melui__ = cmds.menuItem
    def __enter__(self):
        cmds.setParent(self,menu=True)
        return self

    def __exit__(self, type, value, traceback):
        p = self.parent()
        cmds.setParent(p,menu=True)
        return p

def MenuItem(name=None, create=False, **kwargs):
    if PyUI._isBeingCreated(name, create, kwargs):
        cls = CommandMenuItem
    else:
        try:
            uiType = cmds.objectTypeUI(name)
        except RuntimeError:
            cls = SubMenuItem
        else:
            if uiType == 'subMenuItem':
                cls = SubMenuItem
            else:
                cls = CommandMenuItem
    return cls(name, create, **kwargs)

class UITemplate(object):
    """
    from pymel.core import *

    # force deletes the template if it already exists
    template = ui.UITemplate( 'ExampleTemplate', force=True )

    template.define( button, width=100, height=40, align='left' )
    template.define( frameLayout, borderVisible=True, labelVisible=False )

    #    Create a window and apply the template.
    #
    with window():
        with template:
            with columnLayout( rowSpacing=5 ):
                with frameLayout():
                    with columnLayout():
                        button( label='One' )
                        button( label='Two' )
                        button( label='Three' )

                with frameLayout():
                    with columnLayout():
                        button( label='Red' )
                        button( label='Green' )
                        button( label='Blue' )
    """
    def __init__(self, name=None, force=False):
        if name and cmds.uiTemplate( name, exists=True ):
            if force:
                cmds.deleteUI( name, uiTemplate=True )
            else:
                self._name = name
                return
        args = [name] if name else []
        self._name = cmds.uiTemplate( *args )

    def __repr__(self):
        return '%s(%r)' % ( self.__class__.__name__, self._name)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, type, value, traceback):
        self.pop()

    def name(self):
        return self._name

    def push(self):
        cmds.setUITemplate(self._name, pushTemplate=True)

    def pop(self):
        cmds.setUITemplate( popTemplate=True)

    def define(self, uiType, **kwargs):
        """
        uiType can be:
            - a ui function or class
            - the name of a ui function or class
            - a list or tuple of the above
        """
        if isinstance(uiType, (list,tuple)):
            funcs = [ _resolveUIFunc(x) for x in uiType ]
        else:
            funcs = [_resolveUIFunc(uiType)]
        kwargs['defineTemplate'] = self._name
        for func in funcs:
            func(**kwargs)

    @staticmethod
    def exists(name):
        return cmds.uiTemplate( name, exists=True )

class AELoader(type):
    _loaded = []
    def __new__(cls, classname, bases, classdict):
        newcls = super(AELoader, cls).__new__(cls, classname, bases, classdict)
        try:
             nodeType = newcls.nodeType()
        except ValueError:
             _logger.debug("could not determine node type for " + classname)
        else:
             modname = classdict['__module__']
             template = 'AE'+nodeType+'Template'
             cls.makeAEProc(modname, classname, template)
             if template not in cls._loaded:
                 cls._loaded.append(template)
        return newcls
    
    @staticmethod
    def makeAEProc(modname, classname, procname):
        _logger.info("making AE loader procedure: %s" % procname)
        contents = '''global proc %(procname)s( string $nodeName ){
        python("import %(__name__)s;%(__name__)s.AELoader.load('%(modname)s','%(classname)s','" + $nodeName + "')");}'''
        d = locals().copy()
        d['__name__'] = __name__
        import maya.mel as mm
        mm.eval( contents % d )

    @staticmethod
    def load(modname, classname, nodename):
        mod = __import__(modname, globals(), locals(), [classname], -1)
        try:
            cls = getattr(mod,classname)
            cls(nodename)
        except Exception:
            print "failed to load python attribute editor template '%s.%s'" % (modname, classname)
            import traceback
            traceback.print_exc()

    @classmethod
    def loadedTemplates(cls):
        "Return the names of the loaded templates"
        return cls._loaded
    
class AETemplate(object):
    """
    To create an Attribute Editor template using python, do the following:
     	1. create a subclass of `uitypes.AETemplate`
    	2. set its ``_nodeType`` class attribute to the name of the desired node type, or name the class using the
    convention ``AE<nodeType>Template``
    	3. import the module

    AETemplates which do not meet one of the two requirements listed in step 2 will be ignored.  To ensure that your
    Template's node type is being detected correctly, use the ``AETemplate.nodeType()`` class method::

        import AETemplates
        AETemplates.AEmib_amb_occlusionTemplate.nodeType()  

    As a convenience, when pymel is imported it will automatically import the module ``AETemplates``, if it exists,
    thereby causing any AETemplates within it or its sub-modules to be registered. Be sure to import pymel 
    or modules containing your ``AETemplate`` classes before opening the Atrribute Editor for the node types in question.

    To check which python templates are loaded::

    	from pymel.core.uitypes import AELoader
    	print AELoader.loadedTemplates()
    """

    __metaclass__ = AELoader
    
    _nodeType = None
    def __init__(self, nodeName):
        self._nodeName = nodeName

    @property
    def nodeName(self):
        return self._nodeName

    @classmethod
    def nodeType(cls):
        if cls._nodeType:
            return cls._nodeType
        else:
            m = re.match('AE(.+)Template$', cls.__name__)
            if m:
                return m.groups()[0]
            else:
                raise ValueError("You must either name your AETemplate subclass of the form 'AE<nodeType>Template' or set the '_nodeType' class attribute")
    @classmethod
    def controlValue(cls, nodeName, control):
        return cmds.editorTemplate(queryControl=(nodeName,control))
    @classmethod
    def controlLabel(cls, nodeName, control):
        return cmds.editorTemplate(queryLabel=(nodeName,control))
    @classmethod
    def reload(cls):
        "Reload the template. Beware, this reloads the module in which the template exists!"
        nodeType = cls.nodeType()
        form = "AttrEd" + nodeType + "FormLayout"
        exists = cmds.control(form, exists=1) and cmds.formLayout(form, q=1, ca=1)

        if exists:
            sel = cmds.ls(sl=1)
            cmds.select(cl=True)
            cmds.deleteUI(form)
            if sel:
                cmds.select(sel)
        reload(sys.modules[cls.__module__])

    def addControl(self, control, label=None, changeCommand=None, annotation=None, preventOverride=False, dynamic=False):
        args = [control]
        kwargs = {'preventOverride':preventOverride}
        if dynamic:
            kwargs['addDynamicControl'] = True
        else:
            kwargs['addControl'] = True
        if changeCommand:
            if hasattr(changeCommand, '__call__'):
                import pymel.tools.py2mel
                name = self.__class__.__name__ + '_callCustom_changeCommand_' + control
                changeCommand = pymel.tools.py2mel.py2melProc(changeCommand, procName=name, argTypes=['string'])
            args.append(changeCommand)
        if label:
            kwargs['label'] = label
        if annotation:
            kwargs['annotation'] = annotation
        cmds.editorTemplate(*args, **kwargs)
    def callCustom(self, newFunc, replaceFunc, *attrs):
        #cmds.editorTemplate(callCustom=( (newFunc, replaceFunc) + attrs))
        import pymel.tools.py2mel
        if hasattr(newFunc, '__call__'):
            name = self.__class__.__name__ + '_callCustom_newFunc_' + '_'.join(attrs)
            newFunc = pymel.tools.py2mel.py2melProc(newFunc, procName=name, argTypes=['string']*len(attrs))
        if hasattr(replaceFunc, '__call__'):
            name = self.__class__.__name__ + '_callCustom_replaceFunc_' + '_'.join(attrs)
            replaceFunc = pymel.tools.py2mel.py2melProc(replaceFunc, procName=name, argTypes=['string']*len(attrs))
        args = (newFunc, replaceFunc) + attrs
        cmds.editorTemplate(callCustom=1, *args)

    def suppress(self, control):
        cmds.editorTemplate(suppress=control)
    def dimControl(self, nodeName, control, state):
        #nodeName = nodeName if nodeName else self.nodeName
        #print "dim", nodeName
        cmds.editorTemplate(dimControl=(nodeName, control, state))

    def beginLayout(self, name, collapse=True):
        cmds.editorTemplate(beginLayout=name, collapse=collapse)
    def endLayout(self):
        cmds.editorTemplate(endLayout=True)

    def beginScrollLayout(self):
        cmds.editorTemplate(beginScrollLayout=True)
    def endScrollLayout(self):
        cmds.editorTemplate(endScrollLayout=True)

    def beginNoOptimize(self):
        cmds.editorTemplate(beginNoOptimize=True)
    def endNoOptimize(self):
        cmds.editorTemplate(endNoOptimize=True)

    def interruptOptimize(self):
        cmds.editorTemplate(interruptOptimize=True)
    def addSeparator(self):
        cmds.editorTemplate(addSeparator=True)
    def addComponents(self):
        cmds.editorTemplate(addComponents=True)
    def addExtraControls(self, label=None):
        kwargs = {}
        if label:
            kwargs['extraControlsLabel'] = label
        cmds.editorTemplate(addExtraControls=True, **kwargs)

    #TODO: listExtraAttributes


dynModule = _util.LazyLoadModule(__name__, globals())

def _createUIClasses():
    for funcName in _factories.uiClassList:
        # Create Class
        classname = _util.capitalize(funcName)
        try:
            cls = dynModule[classname]
        except KeyError:
            if classname.endswith('Layout'):
                bases = (Layout,)
            elif classname.endswith('Panel'):
                bases = (Panel,)                
            else:
                bases = (PyUI,)
            dynModule[classname] = (_factories.MetaMayaUIWrapper, (classname, bases, {}) )

_createUIClasses()

class VectorFieldGrp( dynModule.FloatFieldGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        if create:
            kwargs.pop('nf', None)
            kwargs['numberOfFields'] = 3
            name = cmds.floatFieldGrp( name, *args, **kwargs)

        return dynModule.FloatFieldGrp.__new__( cls, name, create=False, *args, **kwargs )

    def getVector(self):
        import datatypes
        x = cmds.floatFieldGrp( self, q=1, v1=True )
        y = cmds.floatFieldGrp( self, q=1, v2=True )
        z = cmds.floatFieldGrp( self, q=1, v3=True )
        return datatypes.Vector( [x,y,z] )

    def setVector(self, vec):
        cmds.floatFieldGrp( self, e=1, v1=vec[0], v2=vec[1], v3=vec[2] )

class PathButtonGrp( dynModule.TextFieldButtonGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):

        if create:
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bc', None)
            kwargs.pop('buttonCommand', None)

            name = cmds.textFieldButtonGrp( name, *args, **kwargs)

            def setPathCB(name):
                import windows
                f = windows.promptForPath()
                if f:
                    cmds.textFieldButtonGrp( name, e=1, text=f, forceChangeCommand=True)

            import windows
            cb = windows.Callback( setPathCB, name )
            cmds.textFieldButtonGrp( name, e=1, buttonCommand=cb )

        return dynModule.TextFieldButtonGrp.__new__( cls, name, create=False, *args, **kwargs )

    def setPath(self, path, **kwargs):
        kwargs['forceChangeCommand'] = kwargs.pop('fcc',kwargs.pop('forceChangeCommand',True))
        self.setText( path , **kwargs )

    def getPath(self):
        import system
        return system.Path( self.getText() )

class FolderButtonGrp( PathButtonGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):

        if create:
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bc', None)
            kwargs.pop('buttonCommand', None)

            name = cmds.textFieldButtonGrp( name, *args, **kwargs)

            def setPathCB(name):
                import windows
                f = windows.promptForFolder()
                if f:
                    cmds.textFieldButtonGrp( name, e=1, text=f, forceChangeCommand=True)

            import windows
            cb = windows.Callback( setPathCB, name )
            cmds.textFieldButtonGrp( name, e=1, buttonCommand=cb )

        return dynModule.TextFieldButtonGrp.__new__( cls, name, create=False, *args, **kwargs )

# most of the keys here are names that are only used in certain circumstances
_uiTypesToCommands = {
    'radioCluster':'radioCollection',
    'rowGroupLayout' : 'rowLayout',
    'TcolorIndexSlider' : 'rowLayout',
    'TcolorSlider' : 'rowLayout',
    'floatingWindow' : 'window'
    }

dynModule._lazyModule_update()

