odoo.define('aos_whatsapp_pos.WaPOSOrders', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	class WaPOSOrders extends PosComponent {
		constructor() {
			super(...arguments);
		}

		get highlight() {
			return this.props.order !== this.props.selectedPosOrder ? '' : 'highlight';
		}
	}
	WaPOSOrders.template = 'WaPOSOrders';

	Registries.Component.add(WaPOSOrders);

	return WaPOSOrders;
});
