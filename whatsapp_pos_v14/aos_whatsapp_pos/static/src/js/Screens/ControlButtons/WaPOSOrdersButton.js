odoo.define('aos_whatsapp_pos.WaPOSOrdersButton', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const { useListener } = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');

	class WaPOSOrdersButton extends PosComponent {
		constructor() {
			super(...arguments);
			useListener('click', this.onClick);
		}
		async onClick() {
			await this.showTempScreen('POSOrdersScreen', {
				'selected_partner_id': false 
			});
		}
	}
	WaPOSOrdersButton.template = 'WaPOSOrdersButton';

	ProductScreen.addControlButton({
		component: WaPOSOrdersButton,
		condition: function() {
			return this.env.pos.config.show_order;
		},
	});

	Registries.Component.add(WaPOSOrdersButton);

	return WaPOSOrdersButton;
});
