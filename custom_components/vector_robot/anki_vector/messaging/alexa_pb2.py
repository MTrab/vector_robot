# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: anki_vector/messaging/alexa.proto

# pylint: disable=protected-access
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)
from . import response_status_pb2 as anki__vector_dot_messaging_dot_response__status__pb2

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor.FileDescriptor(
  name='anki_vector/messaging/alexa.proto',
  package='Anki.Vector.external_interface',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=b'\n!anki_vector/messaging/alexa.proto\x12\x1e\x41nki.Vector.external_interface\x1a+anki_vector/messaging/response_status.proto\"\x17\n\x15\x41lexaAuthStateRequest\"\xab\x01\n\x16\x41lexaAuthStateResponse\x12>\n\x06status\x18\x01 \x01(\x0b\x32..Anki.Vector.external_interface.ResponseStatus\x12\x42\n\nauth_state\x18\x02 \x01(\x0e\x32..Anki.Vector.external_interface.AlexaAuthState\x12\r\n\x05\x65xtra\x18\x03 \x01(\t\"#\n\x11\x41lexaOptInRequest\x12\x0e\n\x06opt_in\x18\x01 \x01(\x08\"T\n\x12\x41lexaOptInResponse\x12>\n\x06status\x18\x01 \x01(\x0b\x32..Anki.Vector.external_interface.ResponseStatus\"c\n\x0e\x41lexaAuthEvent\x12\x42\n\nauth_state\x18\x01 \x01(\x0e\x32..Anki.Vector.external_interface.AlexaAuthState\x12\r\n\x05\x65xtra\x18\x02 \x01(\t*\xa2\x01\n\x0e\x41lexaAuthState\x12\x16\n\x12\x41LEXA_AUTH_INVALID\x10\x00\x12\x1c\n\x18\x41LEXA_AUTH_UNINITIALIZED\x10\x01\x12\x1e\n\x1a\x41LEXA_AUTH_REQUESTING_AUTH\x10\x02\x12\x1f\n\x1b\x41LEXA_AUTH_WAITING_FOR_CODE\x10\x03\x12\x19\n\x15\x41LEXA_AUTH_AUTHORIZED\x10\x04\x62\x06proto3'
  ,
  dependencies=[anki__vector_dot_messaging_dot_response__status__pb2.DESCRIPTOR,])

_ALEXAAUTHSTATE = _descriptor.EnumDescriptor(
  name='AlexaAuthState',
  full_name='Anki.Vector.external_interface.AlexaAuthState',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='ALEXA_AUTH_INVALID', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ALEXA_AUTH_UNINITIALIZED', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ALEXA_AUTH_REQUESTING_AUTH', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ALEXA_AUTH_WAITING_FOR_CODE', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ALEXA_AUTH_AUTHORIZED', index=4, number=4,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=538,
  serialized_end=700,
)
_sym_db.RegisterEnumDescriptor(_ALEXAAUTHSTATE)

AlexaAuthState = enum_type_wrapper.EnumTypeWrapper(_ALEXAAUTHSTATE)
ALEXA_AUTH_INVALID = 0
ALEXA_AUTH_UNINITIALIZED = 1
ALEXA_AUTH_REQUESTING_AUTH = 2
ALEXA_AUTH_WAITING_FOR_CODE = 3
ALEXA_AUTH_AUTHORIZED = 4



_ALEXAAUTHSTATEREQUEST = _descriptor.Descriptor(
  name='AlexaAuthStateRequest',
  full_name='Anki.Vector.external_interface.AlexaAuthStateRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=114,
  serialized_end=137,
)


_ALEXAAUTHSTATERESPONSE = _descriptor.Descriptor(
  name='AlexaAuthStateResponse',
  full_name='Anki.Vector.external_interface.AlexaAuthStateResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='Anki.Vector.external_interface.AlexaAuthStateResponse.status', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='auth_state', full_name='Anki.Vector.external_interface.AlexaAuthStateResponse.auth_state', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='extra', full_name='Anki.Vector.external_interface.AlexaAuthStateResponse.extra', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=140,
  serialized_end=311,
)


_ALEXAOPTINREQUEST = _descriptor.Descriptor(
  name='AlexaOptInRequest',
  full_name='Anki.Vector.external_interface.AlexaOptInRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='opt_in', full_name='Anki.Vector.external_interface.AlexaOptInRequest.opt_in', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=313,
  serialized_end=348,
)


_ALEXAOPTINRESPONSE = _descriptor.Descriptor(
  name='AlexaOptInResponse',
  full_name='Anki.Vector.external_interface.AlexaOptInResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='Anki.Vector.external_interface.AlexaOptInResponse.status', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=350,
  serialized_end=434,
)


_ALEXAAUTHEVENT = _descriptor.Descriptor(
  name='AlexaAuthEvent',
  full_name='Anki.Vector.external_interface.AlexaAuthEvent',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='auth_state', full_name='Anki.Vector.external_interface.AlexaAuthEvent.auth_state', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='extra', full_name='Anki.Vector.external_interface.AlexaAuthEvent.extra', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=436,
  serialized_end=535,
)

_ALEXAAUTHSTATERESPONSE.fields_by_name['status'].message_type = anki__vector_dot_messaging_dot_response__status__pb2._RESPONSESTATUS
_ALEXAAUTHSTATERESPONSE.fields_by_name['auth_state'].enum_type = _ALEXAAUTHSTATE
_ALEXAOPTINRESPONSE.fields_by_name['status'].message_type = anki__vector_dot_messaging_dot_response__status__pb2._RESPONSESTATUS
_ALEXAAUTHEVENT.fields_by_name['auth_state'].enum_type = _ALEXAAUTHSTATE
DESCRIPTOR.message_types_by_name['AlexaAuthStateRequest'] = _ALEXAAUTHSTATEREQUEST
DESCRIPTOR.message_types_by_name['AlexaAuthStateResponse'] = _ALEXAAUTHSTATERESPONSE
DESCRIPTOR.message_types_by_name['AlexaOptInRequest'] = _ALEXAOPTINREQUEST
DESCRIPTOR.message_types_by_name['AlexaOptInResponse'] = _ALEXAOPTINRESPONSE
DESCRIPTOR.message_types_by_name['AlexaAuthEvent'] = _ALEXAAUTHEVENT
DESCRIPTOR.enum_types_by_name['AlexaAuthState'] = _ALEXAAUTHSTATE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

AlexaAuthStateRequest = _reflection.GeneratedProtocolMessageType('AlexaAuthStateRequest', (_message.Message,), {
  'DESCRIPTOR' : _ALEXAAUTHSTATEREQUEST,
  '__module__' : 'anki_vector.messaging.alexa_pb2'
  # @@protoc_insertion_point(class_scope:Anki.Vector.external_interface.AlexaAuthStateRequest)
  })
_sym_db.RegisterMessage(AlexaAuthStateRequest)

AlexaAuthStateResponse = _reflection.GeneratedProtocolMessageType('AlexaAuthStateResponse', (_message.Message,), {
  'DESCRIPTOR' : _ALEXAAUTHSTATERESPONSE,
  '__module__' : 'anki_vector.messaging.alexa_pb2'
  # @@protoc_insertion_point(class_scope:Anki.Vector.external_interface.AlexaAuthStateResponse)
  })
_sym_db.RegisterMessage(AlexaAuthStateResponse)

AlexaOptInRequest = _reflection.GeneratedProtocolMessageType('AlexaOptInRequest', (_message.Message,), {
  'DESCRIPTOR' : _ALEXAOPTINREQUEST,
  '__module__' : 'anki_vector.messaging.alexa_pb2'
  # @@protoc_insertion_point(class_scope:Anki.Vector.external_interface.AlexaOptInRequest)
  })
_sym_db.RegisterMessage(AlexaOptInRequest)

AlexaOptInResponse = _reflection.GeneratedProtocolMessageType('AlexaOptInResponse', (_message.Message,), {
  'DESCRIPTOR' : _ALEXAOPTINRESPONSE,
  '__module__' : 'anki_vector.messaging.alexa_pb2'
  # @@protoc_insertion_point(class_scope:Anki.Vector.external_interface.AlexaOptInResponse)
  })
_sym_db.RegisterMessage(AlexaOptInResponse)

AlexaAuthEvent = _reflection.GeneratedProtocolMessageType('AlexaAuthEvent', (_message.Message,), {
  'DESCRIPTOR' : _ALEXAAUTHEVENT,
  '__module__' : 'anki_vector.messaging.alexa_pb2'
  # @@protoc_insertion_point(class_scope:Anki.Vector.external_interface.AlexaAuthEvent)
  })
_sym_db.RegisterMessage(AlexaAuthEvent)


# @@protoc_insertion_point(module_scope)
