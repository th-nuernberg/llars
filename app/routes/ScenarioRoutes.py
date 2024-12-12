import logging
from numbers import Number
from pyexpat.errors import messages
from unicodedata import category
from . import data_blueprint
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash

from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating, UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare,
                       ConsultingCategoryType, UserConsultingCategorySelection)
from sqlalchemy import func
from uuid import uuid4
import uuid
from datetime import datetime
import json




@data_blueprint.route('/scenarios', methods=['GET'])
def get_scenarios():
    pass
