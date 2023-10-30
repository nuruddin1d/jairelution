odoo.define('aos_whatsapp_pos.models', function (require) {
	var models = require('point_of_sale.models');
	models.load_fields('res.partner', ['whatsapp']);
});
