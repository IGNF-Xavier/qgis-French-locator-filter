#! python3  # noqa: E265

"""
Perform network request.
"""

# ############################################################################
# ########## Imports ###############
# ##################################

# Standard library
import json
from functools import lru_cache
from urllib.parse import urlparse, urlunparse

# PyQGIS
from qgis.core import Qgis, QgsBlockingNetworkRequest, QgsNetworkReplyContent
from qgis.PyQt.QtCore import QByteArray, QUrl
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest

# project
from french_locator_filter.toolbelt.log_handler import PlgLogger
from french_locator_filter.toolbelt.preferences import PlgOptionsManager

# ############################################################################
# ########## Classes ###############
# ##################################


class NetworkRequestsManager:
    """Helper on network operations."""

    def __init__(self):
        """Initialization."""
        self.log = PlgLogger().log
        self.ntwk_requester = QgsBlockingNetworkRequest()
        self.plg_settings = PlgOptionsManager.get_plg_settings()

    @lru_cache(maxsize=128)
    def build_url(
        self, request_url: str, request_url_query: str, additional_query: str = None
    ) -> QUrl:
        """Build URL using plugin settings and returns it as QUrl.

        :return: complete URL
        :rtype: QUrl
        """
        parsed_url = urlparse(request_url)

        if additional_query:
            url_query = request_url_query + additional_query
        else:
            url_query = request_url_query

        clean_url = parsed_url._replace(query=url_query)
        return QUrl(urlunparse(clean_url))

    def build_request(
        self, request_url: str = None, request_url_query: str = None, url: QUrl = None
    ) -> QNetworkRequest:
        """Build request object from an url and a query or a already defined QUrl

        Args:
            request_url (str, optional): Request url. Defaults to None.
            request_url_query (str, optional): Request url query. Defaults to None.
            url (QUrl, optional): for url for QNetworkRequest. Request url query and request url are not used. Defaults to None.

        Returns:
            QNetworkRequest: network request object.
        """
        # if URL is not specified, let's use the default one
        if not url:
            url = self.build_url(request_url, request_url_query)

        # create network object
        qreq = QNetworkRequest(url)

        # headers
        headers = {
            b"Accept": bytes(self.plg_settings.http_content_type, "utf8"),
            b"User-Agent": bytes(self.plg_settings.http_user_agent, "utf8"),
        }
        for k, v in headers.items():
            qreq.setRawHeader(k, v)

        return qreq

    def get_error_description_from_reply(
        self, req_reply: QgsNetworkReplyContent
    ) -> str:
        """Define error description from reply.
        Check if `error` and `error_description` are available in request reply content

        :param req_reply: request reply
        :type req_reply: QgsNetworkReplyContent
        :return: error description
        :rtype: str
        """

        data = json.loads(req_reply.content().data().decode("utf-8"))

        if "error" in data:
            error = data["error"]
        else:
            error = req_reply.errorString()

        error_description = ""
        if "error_description" in data:
            error_description = ",".join(data["error_description"])

        if "detail" in data:
            error_description += ",".join(data["detail"])

        return f"{error} : {error_description}"

    def check_request_result(
        self, req_status: QgsBlockingNetworkRequest.ErrorCode
    ) -> QgsNetworkReplyContent:
        """Check request result and content

        :param req_status: request status
        :type req_status: QgsBlockingNetworkRequest.ErrorCode
        :raises ConnectionError: an error occured in request
        :return: request reply content
        :rtype: QgsNetworkReplyContent
        """

        req_reply = self.ntwk_requester.reply()

        # check if request is fine
        if req_status != QgsBlockingNetworkRequest.ErrorCode.NoError:
            error = self.get_error_description_from_reply(req_reply)
            self.log(
                message=error,
                log_level=Qgis.MessageLevel.Critical,
                push=False,
            )
            raise ConnectionError(error)

        # check if reply is fine
        if req_reply.error() != QNetworkReply.NetworkError.NoError:
            error = self.get_error_description_from_reply(req_reply)
            self.log(
                message=error,
                log_level=Qgis.MessageLevel.Critical,
                push=False,
            )
            raise ConnectionError(error)

        return req_reply

    def get_url(self, url: QUrl = None, headers: dict = None) -> QByteArray:
        """Send a get method., using cache and plugin settings.

        :raises ConnectionError: if any problem occurs during feed fetching.
        :raises TypeError: if response mime-type is not valid

        :return: feed response in bytes
        :rtype: QByteArray

        :example:

        .. code-block:: python

            import json
            response_as_dict = json.loads(str(response, "UTF8"))
        """
        # prepare request
        try:
            req = self.build_request(url=url)
            if headers:
                for k, v in headers.items():
                    req.setRawHeader(k, v)
        except Exception as err:
            self.log(
                message=f"Something went wrong during request preparation: {err}",
                log_level=Qgis.MessageLevel.Critical,
                push=False,
            )
            raise err

        # send request
        try:
            req_status = self.ntwk_requester.get(
                request=req,
                forceRefresh=False,
            )

            req_reply = self.check_request_result(req_status)

            self.log(
                message=f"DEBUG - Request to {url} succeeded.",
                log_level=Qgis.MessageLevel.NoLevel,
            )

            # check reply
            req_reply = self.ntwk_requester.reply()
            if b"application/json" not in req_reply.rawHeader(b"Content-Type"):
                raise TypeError(
                    "Response mime-type is '{}' not 'application/json' as required.".format(
                        req_reply.rawHeader(b"Content-type")
                    )
                )

            return req_reply.content()
        except ConnectionError as err:
            raise err
        except Exception as err:
            err_msg = "Houston, we've got a problem: {}".format(err)
            self.log(message=err_msg, log_level=Qgis.MessageLevel.Critical, push=False)
            raise err
