from odoo import api, fields, models, _


class NrcRegion(models.Model):
    _name = 'res.nrc.region'
    _description = "nrc Region"

    name = fields.Char('Region', required=True)


class NrcPrefix(models.Model):
    _name = 'res.nrc.prefix'
    _description = "nrc Prefix"

    name = fields.Char('Prefix', required=True)
    nrc_region = fields.Many2one('res.nrc.region', 'Region')


class NrcType(models.Model):
    _name = 'res.nrc.type'
    _description = "nrc Type"

    name = fields.Char('Type', required=True)
