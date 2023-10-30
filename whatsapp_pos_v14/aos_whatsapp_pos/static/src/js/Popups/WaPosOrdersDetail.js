odoo.define('aos_whatsapp_pos.WaPosOrdersDetail', function(require) {
	'use strict';

	const { useExternalListener } = owl.hooks;
	const PosComponent = require('point_of_sale.PosComponent');
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
	const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { useState } = owl.hooks;

	class WaPosOrdersDetail extends AbstractAwaitablePopup {
		constructor() {
			super(...arguments);
		}
	}
	
	WaPosOrdersDetail.template = 'WaPosOrdersDetail';
	Registries.Component.add(WaPosOrdersDetail);
	return WaPosOrdersDetail;
});
