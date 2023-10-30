odoo.define('aos_whatsapp_pos.WaOrderReprintReceipt', function(require) {
	'use strict';

    const { useRef } = owl.hooks;
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	class WaOrderReprintReceipt extends PosComponent {
		constructor() {
			super(...arguments);
			//const order = this.props.order;
			//const points_won = order.loyalty_points;
			//this.orderReceiptWhatsApp = useRef('order-receipt');
			//const order = this.currentOrder;
			//const loyalty = order.pos.loyalty;
			//const points_won = order.get_won_points();
            //const points_spent = order.get_spent_points();
            //const points_total = order.get_new_total_points();
			//console.log('==order=',points_won,points_spent,points_total)
			//console.log('==order==',this.props.order.config_id)
            //this._receiptEnv = this.props.order.getOrderReceiptEnv();
		}
		/*get receipt() {
			console.log('==receipt==',this.receiptEnv.receipt)
            return this.receiptEnv.receipt;
        }
        get receiptEnv () {
          return this._receiptEnv;
        }*/
		get receiptBarcode(){
			let barcode = this.props.barcode;
			let loyalty = this.props.loyalty;
			console.log('-=-',loyalty)
			$("#barcode_print1").barcode(
				barcode, // Value barcode (dependent on the type of barcode)
				"code128" // type (string)
			);
		return true
		}
	}
	WaOrderReprintReceipt.template = 'WaOrderReprintReceipt';

	Registries.Component.add(WaOrderReprintReceipt);

	return WaOrderReprintReceipt;
});
