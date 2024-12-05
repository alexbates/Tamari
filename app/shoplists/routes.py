from flask import render_template, flash, redirect, url_for, request
from flask_babel import _
from app import app, db, limiter
from app.shoplists.forms import AddListForm, AddListItemForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Shoplist, Listitem
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import secrets, time, random, os, requests, re, urllib.request
from app.shoplists import bp
from config import Config

@bp.route('/shopping-lists', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def shoppingLists():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    lists = user.shop_lists.order_by(Shoplist.label).all()
    query_string = request.args.get('list')
    if query_string is None:
        list = user.shop_lists.filter_by(label='Miscellaneous').first()
    else:
        list = user.shop_lists.filter_by(label=query_string).first()
    try:
        items = list.list_items.order_by(Listitem.item).all()
    except:
        items = []
    try:
        items_tobuy = user.list_items.filter_by(list_id=list.id, complete=0).all()
        items_comp = user.list_items.filter_by(list_id=list.id, complete=1).all()
    except:
        items_tobuy = []
        items_comp = []
    form = AddListForm()
    form2 = AddListItemForm(prefix='a')
    lists_arr = []
    for thing in lists:
        curr_list = thing.label
        lists_arr.append(curr_list)
    items_arr = []
    for thing in items:
        curr_item = thing.item
        items_arr.append(curr_item)
    if form.submitlist.data and form.validate_on_submit():
        if form.newlist.data in lists_arr:
            flash('Error: ' + _('the shopping list you entered already exists.'))
        elif len(lists_arr) > 19:
            flash('Error: ' + _('you are limited to 20 shopping lists.'))
        else:
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(4)
                hex_exist = Shoplist.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            sel_list = Shoplist(hex_id=hex_string, label=form.newlist.data, user_id=current_user.id)
            db.session.add(sel_list)
            db.session.commit()
            flash(_('The shopping list has been added.'))
        return redirect(url_for('shoplists.shoppingLists', list=list.label))
    if form2.submititem.data and form2.validate_on_submit():
        if form2.newitem.data in items_arr:
            flash('Error: ' + _('the list item you entered already exists.'))
        elif len(items_arr) > 99:
            flash('Error: ' + _('you are limited to 100 items per list.'))
        else:
            hex_valid2 = 0
            while hex_valid2 == 0:
                hex_string2 = secrets.token_hex(5)
                hex_exist2 = Listitem.query.filter_by(hex_id=hex_string2).first()
                if hex_exist2 is None:
                    hex_valid2 = 1
            sel_item = Listitem(hex_id=hex_string2, item=form2.newitem.data, user_id=current_user.id, complete=0, list_id=list.id)
            db.session.add(sel_item)
            db.session.commit()
            flash(_('The item has been added.'))
        return redirect(url_for('shoplists.shoppingLists', list=list.label))
    return render_template('shopping-lists.html', title=_('Shopping Lists'),
        mdescription=_('Display all saved shopping lists and list items for the selected list.'), lists=lists,
        query_string=query_string, list=list, lists_arr=lists_arr, items=items, items_tobuy=items_tobuy,
        items_comp=items_comp, form=form, form2=form2)

@bp.route('/m/shopping-list/<listname>', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def mobileList(listname):
    user = User.query.filter_by(email=current_user.email).first_or_404()
    list = user.shop_lists.filter_by(label=listname).first()
    if list is None:
        flash('Error: ' + _('the list you requested does not exist.'))
    items = list.list_items.order_by(Listitem.item).all()
    items_tobuy = user.list_items.filter_by(list_id=list.id, complete=0).all()
    items_comp = user.list_items.filter_by(list_id=list.id, complete=1).all()
    form = AddListItemForm()
    items_arr = []
    for thing in items:
        curr_item = thing.item
        items_arr.append(curr_item)
    if form.submititem.data and form.validate_on_submit():
        if form.newitem.data in items_arr:
            flash('Error: ' + _('the list item you entered already exists.'))
        elif len(items_arr) > 69:
            flash('Error: ' + _('you are limited to 70 items per list.'))
        else:
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(5)
                hex_exist = Listitem.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            sel_item = Listitem(hex_id=hex_string, item=form.newitem.data, user_id=current_user.id, complete=0, list_id=list.id)
            db.session.add(sel_item)
            db.session.commit()
            flash(_('The item has been added.'))
        return redirect(url_for('shoplists.mobileList', listname=list.label))
    return render_template('mobile-shopping-list.html', title=listname,
        mdescription=_('Display all list items for the selected shopping list.'), list=list, items=items,
        items_tobuy=items_tobuy, items_comp=items_comp, form=form)

@bp.route('/remove-list/<mobile>/<hexid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def removeList(hexid, mobile):
    list = Shoplist.query.filter_by(hex_id=hexid).first()
    user = User.query.filter_by(email=current_user.email).first()
    try:
        listitems = Listitem.query.filter_by(list_id=list.id).all()
    except:
        listitems = []
    if list is None:
        flash('Error: ' + _('shopping list does not exist.'))
    elif list.label == 'Miscellaneous':
        flash('Error: Miscellaneous ' + _('cannot be deleted because it is the default shopping list.'))
    else:
        if list.user_id == current_user.id:
            for item in listitems:
                db.session.delete(item)
            db.session.delete(list)
            db.session.commit()
            flash(_('Shopping list has been removed.'))
        else:
            flash('Error: ' + _('shopping list does not exist.'))
    if mobile == '0':
        return redirect(url_for('shoplists.shoppingLists'))
    else:
        return redirect(url_for('shoplists.mobileList', listname='Miscellaneous'))

@bp.route('/remove-item/<mobile>/<hexid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def removeListitem(hexid, mobile):
    listitem = Listitem.query.filter_by(hex_id=hexid).first()
    try:
        list = Shoplist.query.filter_by(id=listitem.list_id).first()
    except:
        list = None
    if listitem is None:
        flash('Error: ' + _('item does not exist.'))
    else:
        if listitem.user_id == current_user.id:
            db.session.delete(listitem)
            db.session.commit()
            flash(_('The item has been removed.'))
        else:
            flash('Error: ' + _('item does not exist.'))
    if mobile == '0':
        return redirect(url_for('shoplists.shoppingLists', list=list.label))
    else:
        return redirect(url_for('shoplists.mobileList', listname=list.label))

@bp.route('/mark-item/<mobile>/<hexid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def markItem(hexid, mobile):
    listitem = Listitem.query.filter_by(hex_id=hexid).first()
    list = Shoplist.query.filter_by(id=listitem.list_id).first()
    if listitem is None:
        flash('Error: ' + _('item does not exist.'))
    else:
        if listitem.user_id == current_user.id:
            if listitem.complete == 0:
                listitem.complete = 1
                db.session.commit()
            else:
                listitem.complete = 0
                db.session.commit()
        else:
            flash('Error: ' + _('item does not exist.'))
    if mobile == '0':
        return redirect(url_for('shoplists.shoppingLists', list=list.label))
    else:
        return redirect(url_for('shoplists.mobileList', listname=list.label))
