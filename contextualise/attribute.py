from flask import (Blueprint, render_template, request, flash, url_for)
from flask_login import current_user
from flask_security import login_required
from topicdb.core.models.attribute import Attribute
from topicdb.core.models.datatype import DataType
from topicdb.core.store.retrievaloption import RetrievalOption
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from contextualise.topic_store import get_topic_store

bp = Blueprint('attribute', __name__)


@bp.route('/attributes/<map_identifier>/<topic_identifier>')
@login_required
def index(map_identifier, topic_identifier):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    attributes = []
    entity_attributes = topic_store.get_attributes(map_identifier, topic_identifier)

    for entity_attribute in entity_attributes:
        attributes.append({'identifier': entity_attribute.identifier,
                           'name': entity_attribute.name,
                           'value': entity_attribute.value,
                           'type': str(entity_attribute.data_type).lower(),
                           'scope': entity_attribute.scope})

    entity_type = 'topic'
    return_url = 'topic.view'

    return render_template('attribute/index.html',
                           topic_map=topic_map,
                           topic=topic,
                           entity_type=entity_type,
                           return_url=return_url,
                           attributes=attributes)


@bp.route('/attributes/<entity_type>/<map_identifier>/<topic_identifier>/<entity_identifier>')
@login_required
def entity_index(map_identifier, topic_identifier, entity_identifier, entity_type):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    entity = topic_store.get_association(map_identifier, entity_identifier,
                                         resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if entity is None:
        entity = topic_store.get_occurrence(map_identifier, entity_identifier)

    if entity is None:
        abort(404)

    return_url = None
    if entity_type == 'association':
        return_url = 'association.index'
    elif entity_type == 'image':
        return_url = 'image.index'
    elif entity_type == '3d-scene':
        return_url = 'three_d.index'
    elif entity_type == 'file':
        return_url = 'file.index'
    elif entity_type == 'link':
        return_url = 'link.index'
    elif entity_type == 'video':
        return_url = 'video.index'

    attributes = []
    entity_attributes = topic_store.get_attributes(map_identifier, entity_identifier)

    for entity_attribute in entity_attributes:
        attributes.append({'identifier': entity_attribute.identifier,
                           'name': entity_attribute.name,
                           'value': entity_attribute.value,
                           'type': str(entity_attribute.data_type).lower(),
                           'scope': entity_attribute.scope})

    return render_template('attribute/index.html',
                           topic_map=topic_map,
                           topic=topic,
                           entity=entity,
                           entity_type=entity_type,
                           return_url=return_url,
                           attributes=attributes)


@bp.route('/attributes/add/<map_identifier>/<topic_identifier>', methods=('GET', 'POST'))
@login_required
def add(map_identifier, topic_identifier):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    form_attribute_name = ''
    form_attribute_value = ''
    form_attribute_type = ''
    form_attribute_scope = '*'

    error = 0

    if request.method == 'POST':
        form_attribute_name = request.form['attribute-name'].strip()
        form_attribute_value = request.form['attribute-value'].strip()
        form_attribute_type = request.form['attribute-type']
        form_attribute_scope = request.form['attribute-scope'].strip()

        # If no values have been provided set their default values
        if not form_attribute_scope:
            form_attribute_scope = '*'  # Universal scope

        # Validate form inputs
        if not form_attribute_name:
            error = error | 1
        if not form_attribute_value:
            error = error | 2
        if not topic_store.topic_exists(topic_map.identifier, form_attribute_scope):
            error = error | 4

        if error != 0:
            flash(
                'An error occurred when submitting the form. Please review the warnings and fix accordingly.',
                'warning')
        else:
            attribute = Attribute(form_attribute_name, form_attribute_value, topic.identifier,
                                  data_type=DataType[form_attribute_type])

            # Persist objects to the topic store
            topic_store.set_attribute(topic_map.identifier, attribute)

            flash('Attribute successfully added.', 'success')
            return redirect(
                url_for('attribute.index', map_identifier=topic_map.identifier, topic_identifier=topic.identifier))

    entity_type = 'topic'
    post_url = 'attribute.add'
    cancel_url = 'attribute.index'

    return render_template('attribute/add.html',
                           error=error,
                           topic_map=topic_map,
                           topic=topic,
                           entity_type=entity_type,
                           post_url=post_url,
                           cancel_url=cancel_url,
                           attribute_name=form_attribute_name,
                           attribute_value=form_attribute_value,
                           attribute_type=form_attribute_type,
                           attribute_scope=form_attribute_scope)


@bp.route('/attributes/add/<entity_type>/<map_identifier>/<topic_identifier>/<entity_identifier>',
          methods=('GET', 'POST'))
@login_required
def entity_add(map_identifier, topic_identifier, entity_identifier, entity_type):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    entity = topic_store.get_association(map_identifier, entity_identifier,
                                         resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if entity is None:
        entity = topic_store.get_occurrence(map_identifier, entity_identifier)

    if entity is None:
        abort(404)

    form_attribute_name = ''
    form_attribute_value = ''
    form_attribute_type = ''
    form_attribute_scope = '*'

    error = 0

    if request.method == 'POST':
        form_attribute_name = request.form['attribute-name'].strip()
        form_attribute_value = request.form['attribute-value'].strip()
        form_attribute_type = request.form['attribute-type']
        form_attribute_scope = request.form['attribute-scope'].strip()

        # If no values have been provided set their default values
        if not form_attribute_scope:
            form_attribute_scope = '*'  # Universal scope

        # Validate form inputs
        if not form_attribute_name:
            error = error | 1
        if not form_attribute_value:
            error = error | 2
        if not topic_store.topic_exists(topic_map.identifier, form_attribute_scope):
            error = error | 4

        if error != 0:
            flash(
                'An error occurred when submitting the form. Please review the warnings and fix accordingly.',
                'warning')
        else:
            attribute = Attribute(form_attribute_name, form_attribute_value, entity.identifier,
                                  data_type=DataType[form_attribute_type])

            # Persist objects to the topic store
            topic_store.set_attribute(topic_map.identifier, attribute)

            flash('Attribute successfully added.', 'success')
            return redirect(
                url_for('attribute.entity_index', map_identifier=topic_map.identifier,
                        topic_identifier=topic.identifier, entity_identifier=entity.identifier,
                        entity_type=entity_type))

    post_url = 'attribute.entity_add'
    cancel_url = 'attribute.entity_index'

    return render_template('attribute/add.html',
                           error=error,
                           topic_map=topic_map,
                           topic=topic,
                           entity=entity,
                           entity_type=entity_type,
                           post_url=post_url,
                           cancel_url=cancel_url,
                           attribute_name=form_attribute_name,
                           attribute_value=form_attribute_value,
                           attribute_type=form_attribute_type,
                           attribute_scope=form_attribute_scope)


@bp.route('/attributes/edit/<map_identifier>/<topic_identifier>/<attribute_identifier>', methods=('GET', 'POST'))
@login_required
def edit(map_identifier, topic_identifier, attribute_identifier):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    attribute = topic_store.get_attribute(map_identifier, attribute_identifier)
    if attribute is None:
        abort(404)

    form_attribute_name = attribute.name
    form_attribute_value = attribute.value
    form_attribute_type = str(attribute.data_type).capitalize()
    form_attribute_scope = attribute.scope

    error = 0

    if request.method == 'POST':
        form_attribute_name = request.form['attribute-name'].strip()
        form_attribute_value = request.form['attribute-value'].strip()
        form_attribute_type = request.form['attribute-type']
        form_attribute_scope = request.form['attribute-scope'].strip()

        # If no values have been provided set their default values
        if not form_attribute_scope:
            form_attribute_scope = '*'  # Universal scope

        # Validate form inputs
        if not form_attribute_name:
            error = error | 1
        if not form_attribute_value:
            error = error | 2
        if not topic_store.topic_exists(topic_map.identifier, form_attribute_scope):
            error = error | 4

        if error != 0:
            flash(
                'An error occurred when submitting the form. Please review the warnings and fix accordingly.',
                'warning')
        else:
            # Update the attribute by deleting the existing attribute and adding a new one
            topic_store.delete_attribute(map_identifier, attribute.identifier)
            updated_attribute = Attribute(form_attribute_name, form_attribute_value, topic.identifier,
                                          data_type=DataType[form_attribute_type])
            topic_store.set_attribute(topic_map.identifier, updated_attribute)

            flash('Attribute successfully updated.', 'success')
            return redirect(
                url_for('attribute.index', map_identifier=topic_map.identifier, topic_identifier=topic.identifier))

    entity_type = 'topic'
    data_types = [('STRING', 'String'), ('NUMBER', 'Number'), ('TIMESTAMP', 'Timestamp'), ('BOOLEAN', 'Boolean')]
    post_url = 'attribute.edit'
    cancel_url = 'attribute.index'

    return render_template('attribute/edit.html',
                           error=error,
                           topic_map=topic_map,
                           topic=topic,
                           attribute=attribute,
                           entity_type=entity_type,
                           data_types=data_types,
                           post_url=post_url,
                           cancel_url=cancel_url,
                           attribute_name=form_attribute_name,
                           attribute_value=form_attribute_value,
                           attribute_type=form_attribute_type,
                           attribute_scope=form_attribute_scope)


@bp.route(
    '/attributes/edit/<entity_type>/<map_identifier>/<topic_identifier>/<entity_identifier>/<attribute_identifier>',
    methods=('GET', 'POST'))
@login_required
def entity_edit(map_identifier, topic_identifier, entity_identifier, attribute_identifier, entity_type):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    entity = topic_store.get_association(map_identifier, entity_identifier,
                                         resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if entity is None:
        entity = topic_store.get_occurrence(map_identifier, entity_identifier)

    if entity is None:
        abort(404)

    attribute = topic_store.get_attribute(map_identifier, attribute_identifier)
    if attribute is None:
        abort(404)

    form_attribute_name = attribute.name
    form_attribute_value = attribute.value
    form_attribute_type = str(attribute.data_type).capitalize()
    form_attribute_scope = attribute.scope

    error = 0

    if request.method == 'POST':
        form_attribute_name = request.form['attribute-name'].strip()
        form_attribute_value = request.form['attribute-value'].strip()
        form_attribute_type = request.form['attribute-type']
        form_attribute_scope = request.form['attribute-scope'].strip()

        # If no values have been provided set their default values
        if not form_attribute_scope:
            form_attribute_scope = '*'  # Universal scope

        # Validate form inputs
        if not form_attribute_name:
            error = error | 1
        if not form_attribute_value:
            error = error | 2
        if not topic_store.topic_exists(topic_map.identifier, form_attribute_scope):
            error = error | 4

        if error != 0:
            flash(
                'An error occurred when submitting the form. Please review the warnings and fix accordingly.',
                'warning')
        else:
            # Update the attribute by deleting the existing attribute and adding a new one
            topic_store.delete_attribute(map_identifier, attribute.identifier)
            updated_attribute = Attribute(form_attribute_name, form_attribute_value, entity.identifier,
                                          data_type=DataType[form_attribute_type])
            topic_store.set_attribute(topic_map.identifier, updated_attribute)

            flash('Attribute successfully updated.', 'success')
            return redirect(
                url_for('attribute.entity_index', map_identifier=topic_map.identifier,
                        topic_identifier=topic.identifier, entity_identifier=entity.identifier,
                        entity_type=entity_type))

    data_types = [('STRING', 'String'), ('NUMBER', 'Number'), ('TIMESTAMP', 'Timestamp'), ('BOOLEAN', 'Boolean')]
    post_url = 'attribute.entity_edit'
    cancel_url = 'attribute.entity_index'

    return render_template('attribute/edit.html',
                           error=error,
                           topic_map=topic_map,
                           topic=topic,
                           attribute=attribute,
                           entity=entity,
                           entity_type=entity_type,
                           data_types=data_types,
                           post_url=post_url,
                           cancel_url=cancel_url,
                           attribute_name=form_attribute_name,
                           attribute_value=form_attribute_value,
                           attribute_type=form_attribute_type,
                           attribute_scope=form_attribute_scope)


@bp.route('/attributes/delete/<map_identifier>/<topic_identifier>/<attribute_identifier>', methods=('GET', 'POST'))
@login_required
def delete(map_identifier, topic_identifier, attribute_identifier):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    attribute = topic_store.get_attribute(map_identifier, attribute_identifier)
    if attribute is None:
        abort(404)

    form_attribute_name = attribute.name
    form_attribute_value = attribute.value
    form_attribute_type = str(attribute.data_type).capitalize()
    form_attribute_scope = attribute.scope

    if request.method == 'POST':
        # Delete attribute from topic store
        topic_store.delete_attribute(map_identifier, attribute.identifier)

        flash('Attribute successfully deleted.', 'warning')
        return redirect(
            url_for('attribute.index', map_identifier=topic_map.identifier, topic_identifier=topic.identifier))

    entity_type = 'topic'
    post_url = 'attribute.delete'
    cancel_url = 'attribute.index'

    return render_template('attribute/delete.html',
                           topic_map=topic_map,
                           topic=topic,
                           attribute=attribute,
                           entity_type=entity_type,
                           post_url=post_url,
                           cancel_url=cancel_url,
                           attribute_name=form_attribute_name,
                           attribute_value=form_attribute_value,
                           attribute_type=form_attribute_type,
                           attribute_scope=form_attribute_scope)


@bp.route(
    '/attributes/delete/<entity_type>/<map_identifier>/<topic_identifier>/<entity_identifier>/<attribute_identifier>',
    methods=('GET', 'POST'))
@login_required
def entity_delete(map_identifier, topic_identifier, entity_identifier, attribute_identifier, entity_type):
    topic_store = get_topic_store()
    topic_map = topic_store.get_topic_map(map_identifier)

    if topic_map is None:
        abort(404)

    if current_user.id != topic_map.user_identifier:
        abort(403)

    topic = topic_store.get_topic(map_identifier, topic_identifier,
                                  resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if topic is None:
        abort(404)

    entity = topic_store.get_association(map_identifier, entity_identifier,
                                         resolve_attributes=RetrievalOption.RESOLVE_ATTRIBUTES)
    if entity is None:
        entity = topic_store.get_occurrence(map_identifier, entity_identifier)

    if entity is None:
        abort(404)

    attribute = topic_store.get_attribute(map_identifier, attribute_identifier)
    if attribute is None:
        abort(404)

    form_attribute_name = attribute.name
    form_attribute_value = attribute.value
    form_attribute_type = str(attribute.data_type).capitalize()
    form_attribute_scope = attribute.scope

    if request.method == 'POST':
        # Delete attribute from topic store
        topic_store.delete_attribute(map_identifier, attribute.identifier)

        flash('Attribute successfully deleted.', 'warning')
        return redirect(
            url_for('attribute.entity_index', map_identifier=topic_map.identifier,
                    topic_identifier=topic.identifier, entity_identifier=entity.identifier,
                    entity_type=entity_type))

    post_url = 'attribute.entity_delete'
    cancel_url = 'attribute.entity_index'

    return render_template('attribute/delete.html',
                           topic_map=topic_map,
                           topic=topic,
                           entity=entity,
                           attribute=attribute,
                           entity_type=entity_type,
                           post_url=post_url,
                           cancel_url=cancel_url,
                           attribute_name=form_attribute_name,
                           attribute_value=form_attribute_value,
                           attribute_type=form_attribute_type,
                           attribute_scope=form_attribute_scope)