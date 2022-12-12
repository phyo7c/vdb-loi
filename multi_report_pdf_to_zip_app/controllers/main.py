# -*- coding: utf-8 -*-
from odoo import http
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval
from odoo.http import request,serialize_exception as _serialize_exception,content_disposition
from odoo.addons.web.controllers.main import ReportController
import os
import time
import base64
import zipfile
import json
import mimetypes
from werkzeug.urls import url_decode


class ReportControllerInherited(ReportController):

	@http.route([
		'/report/<converter>/<reportname>',
		'/report/<converter>/<reportname>/<docids>',
	], type='http', auth='user', website=True)
	def report_routes(self, reportname, docids=None, converter=None, **data):
		if converter == "py3o":
			context = dict(request.env.context)

			if docids:
				docids = [int(i) for i in docids.split(",")]
			if data.get("options"):
				data.update(json.loads(data.pop("options")))
			if data.get("context"):
				# Ignore 'lang' here, because the context in data is the
				# one from the webclient *but* if the user explicitely wants to
				# change the lang, this mechanism overwrites it.
				data["context"] = json.loads(data["context"])
				if data["context"].get("lang"):
					del data["context"]["lang"]
				context.update(data["context"])

			ir_action = request.env["ir.actions.report"]
			action_py3o_report = ir_action.get_from_report_name(
				reportname, "py3o"
			).with_context(context)
			if not action_py3o_report:
				raise exceptions.HTTPException(
					description="Py3o action report not found for report_name "
								"%s" % reportname
				)
			res, filetype = action_py3o_report._render(docids, data)
			filename = action_py3o_report.gen_report_download_filename(docids, data)
			if not filename.endswith(filetype):
				filename = "{}.{}".format(filename, filetype)
			content_type = mimetypes.guess_type("x." + filetype)[0]
			http_headers = [
				("Content-Type", content_type),
				("Content-Length", len(res)),
				("Content-Disposition", content_disposition(filename)),
			]
			return request.make_response(res, headers=http_headers)
		report = request.env['ir.actions.report']._get_report_from_name(reportname)
		context = dict(request.env.context)
		if docids:
			docids = [int(i) for i in docids.split(',')]
		if data.get('options'):
			data.update(json.loads(data.pop('options')))
		if data.get('context'):
			# Ignore 'lang' here, because the context in data is the one from the webclient *but* if
			# the user explicitely wants to change the lang, this mechanism overwrites it.
			data['context'] = json.loads(data['context'])
			if data['context'].get('lang'):
				del data['context']['lang']
			context.update(data['context'])
		if converter == 'html':
			html = report.with_context(context).render_qweb_html(docids, data=data)[0]
			return request.make_response(html)
		elif converter == 'pdf':
			if report.is_zip:
				report = request.env['ir.actions.report']._get_report_from_name(reportname)
				original_filename = "%s.%s" % (report.name, converter)
				dir_path = os.path.dirname(os.path.realpath(__file__))
				filenames = []
				for docid in docids:
					pdf = report.with_context(context)._render_qweb_pdf(docid, data=data)
					obj = request.env[report.model].browse(docid)
					filename = original_filename
					if report.print_report_name:
						report_name = safe_eval(report.print_report_name, {'object': obj})
						filename = "%s.%s" % (report_name, converter)
						filename = filename.replace("/",",")
						filenames.append(filename)
					with open('%s'%(filename), "wb") as outfile:
						outfile.write(pdf[0])
				with zipfile.ZipFile('baapuki.zip', 'w') as myzip:
					for fn in filenames:
						myzip.write(fn)
				with open("baapuki.zip", "rb") as f:
					converts = f.read()
					encoded = base64.b64encode(converts)
				for fn1 in filenames:
					try:
						os.remove(fn1)
					except Exception as e:
						continue
				os.remove('baapuki.zip')
				decode_content = base64.b64decode(encoded)
				pdfhttpheaders = [('Content-Type', 'application/zip'), ('Content-Length', len(decode_content))]
				return request.make_response(decode_content, headers=pdfhttpheaders)
			else:
				pdf = report.with_context(context)._render_qweb_pdf(docids, data=data)[0]
				pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
				return request.make_response(pdf, headers=pdfhttpheaders)
		elif converter == 'text':
			text = report.with_context(context).render_qweb_text(docids, data=data)[0]
			texthttpheaders = [('Content-Type', 'text/plain'), ('Content-Length', len(text))]
			return request.make_response(text, headers=texthttpheaders)
		else:
			raise werkzeug.exceptions.HTTPException(description='Converter %s not implemented.' % converter)

	@http.route(['/report/download'], type='http', auth="user")
	def report_download(self, data, token):
		"""This function is used by 'action_manager_report.js' in order to trigger the download of
		a pdf/controller report.

		:param data: a javascript array JSON.stringified containg report internal url ([0]) and
		type [1]
		:returns: Response with a filetoken cookie and an attachment header
		"""
		requestcontent = json.loads(data)
		url, type = requestcontent[0], requestcontent[1]
		if type == "py3o":
			try:
				reportname = url.split("/report/py3o/")[1].split("?")[0]
				docids = None
				if "/" in reportname:
					reportname, docids = reportname.split("/")

				if docids:
					# Generic report:
					response = self.report_routes(
						reportname, docids=docids, converter="py3o"
					)
				else:
					# Particular report:
					# decoding the args represented in JSON
					data = list(url_decode(url.split("?")[1]).items())
					response = self.report_routes(
						reportname, converter="py3o", **dict(data)
					)
				response.set_cookie("fileToken", token)
				return response
			except Exception as e:
				se = _serialize_exception(e)
				error = {"code": 200, "message": "Odoo Server Error", "data": se}
				return request.make_response(html_escape(json.dumps(error)))
		try:
			if type in ['qweb-pdf', 'qweb-text']:
				converter = 'pdf' if type == 'qweb-pdf' else 'text'
				extension = 'pdf' if type == 'qweb-pdf' else 'txt'

				pattern = '/report/pdf/' if type == 'qweb-pdf' else '/report/text/'
				reportname = url.split(pattern)[1].split('?')[0]

				docids = None
				temp_lists = []
				if '/' in reportname:
					reportname, docids = reportname.split('/')
				else:
					data_lists = url.split('active_ids')[1].split('%')
					for data_list in data_lists:
						rang = len(data_list)
						if rang > 2:
							temp_lists.append(data_list[2:])
				if temp_lists:
					flag = True
					for temp_list in temp_lists:
						if flag:
							docids = temp_list
							flag = False
						else:
							docids += ',' + temp_list
				url_cutoff = url.split('fiscal_year_id')
				fiscal_year = {}
				if len(url_cutoff) > 1:
					fiscal_cutoff = url_cutoff[1].split('emp')
					if fiscal_cutoff:
						fiscal_years = fiscal_cutoff[0].split('%')
						if fiscal_years:
							for data_list in fiscal_years:
								rang = len(data_list)
								if rang > 2:
									fiscal_year_id = int(data_list[2:])
									fiscal_year['fiscal_year_id'] = fiscal_year_id
				if docids and not fiscal_year:
					# Generic report:
					response = self.report_routes(reportname, docids=docids, converter=converter)
				elif docids and fiscal_year:
					response = self.report_routes(reportname, docids=docids, converter=converter, **fiscal_year)
				else:
					# Particular report:
					data = url_decode(url.split('?')[1]).items()  # decoding the args represented in JSON
					response = self.report_routes(reportname, converter=converter, **dict(data))

				report = request.env['ir.actions.report']._get_report_from_name(reportname)
				filename = "%s.%s" % (report.name, extension)

				ids = [int(x) for x in docids.split(",")]

				if report.is_zip:
					filename = "%s.%s" % (report.name, 'zip')
					response.headers.add('Content-Disposition', content_disposition(filename))
				else:
					if docids:
						obj = request.env[report.model].browse(ids)
						if report.print_report_name and not len(obj) > 1:
							report_name = safe_eval(report.print_report_name, {'object': obj})
							filename = "%s.%s" % (report_name, extension)
					response.headers.add('Content-Disposition', content_disposition(filename))
					
				response.set_cookie('fileToken', token)
				return response
			else:
				return
		except Exception as e:
			se = _serialize_exception(e)
			error = {
				'code': 200,
				'message': "Odoo Server Error",
				'data': se
			}
			return request.make_response(html_escape(json.dumps(error)))
