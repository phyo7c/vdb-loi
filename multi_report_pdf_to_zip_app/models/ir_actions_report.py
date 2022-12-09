# -*- coding: utf-8 -*-

from odoo import fields, models, api
from PyPDF2 import PdfFileWriter, PdfFileReader
from odoo.tools.safe_eval import safe_eval
import requests
import sys
import os



class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'


    is_zip = fields.Boolean('Is Zip?')

    # def render_qweb_pdf(self, res_ids=None, data=None):
    #     res = super(IrActionsReport, self).render_qweb_pdf(res_ids=res_ids, data=data)
    #     print ("res==============",res)
    #     return res

    # def render_qweb_pdf(self, res_ids=None, data=None):
    #     res = super(IrActionsReport, self).render_qweb_pdf(res_ids=res_ids, data=data)
    #     if self.is_zip:
    #         # models_ids= self.env[self.model].search([('id', 'in', res_ids)])
    #         # for models_id in models_ids:
    #         #     name = safe_eval(self.print_report_name, ({'object': models_id}))
    #         #     print ("name=====================",name)
    #         #     scriptPath = sys.path[0]
    #         #     # downloadPath = os.path.join(scriptPath, '../Downloads/')
    #         #     # url = sys.argv[1]
    #         #     fileName = sys.argv[2]
    #         #     with open(fileName, "wb") as file:
    #         #         response = requests.get(downloadPath)
    #         #         print ("response------------------",response)
    #         #     #     file.write(response.content)    
    #     return res

