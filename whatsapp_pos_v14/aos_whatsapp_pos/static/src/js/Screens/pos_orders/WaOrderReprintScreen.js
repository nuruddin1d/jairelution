odoo.define('aos_whatsapp_pos.WaOrderReprintScreen', function (require) {
	'use strict';

    const { useRef } = owl.hooks;
    const { useListener } = require('web.custom_hooks');
    const { useContext } = owl.hooks;
	const { Printer } = require('point_of_sale.Printer');
	const ReceiptScreen = require('point_of_sale.ReceiptScreen');
	const Registries = require('point_of_sale.Registries');

	const WaOrderReprintScreen = (ReceiptScreen) => {
		class WaOrderReprintScreen extends ReceiptScreen {
			constructor() {
				super(...arguments);
				this.orderReceiptWhatsApp = useRef('order-receipt');
				const order = this.currentOrder;
				//const loyalty = order.pos.loyalty;
				//const points_won = order.get_won_points();
                //const points_spent = order.get_spent_points();
                //const points_total = order.get_new_total_points();
                const client = order.get_client;
				const orderName = order.get_name();
				const pos_config = this.env.pos.config;
				//console.log('==order=',points_won,points_spent,points_total)
				//console.log('==order==',order)
				let message = pos_config.whatsapp_default_message.replace("_CUSTOMER_", this.props.client_name || 'Customer');
				this.orderUiState = useContext(order.uiState.ReceiptScreen);
				this.orderUiState.inputWhatsapp = this.orderUiState.inputWhatsapp || (this.props.client_whatsapp) || '';
				console.log('=WaOrderReprintScreen=',this.orderUiState.inputWhatsapp)
                this.orderUiState.inputMessage = message + ' ' + orderName +'.';//'Dear *' + (this.props.client_name || 'Customer') + '*, Here is your electronic ticket for the '+ orderName +'.';
			}
			
            async onreSendWhatsapp() {
                if (!this.orderUiState.inputWhatsapp) {
                    this.orderUiState.whatsappSuccessful = false;
                    this.orderUiState.whatsappNotice = this.env._t('Whatsapp number is empty.');
                    return;
                }
                try {
                    await this._resendWhatsappToCustomer();
					console.log('==RESEND==')
                    this.orderUiState.whatsappSuccessful = true;
                    this.orderUiState.whatsappNotice = 'Whatsapp sent.'
                } catch (error) {
					console.log('==REERROR==',error)
                    this.orderUiState.whatsappSuccessful = false;
                    this.orderUiState.whatsappNotice = 'Sending Whatsapp failed. Please try again.'
                }
                //console.log('=onSendWhatsapp=',this._sendWhatsappToCustomer())
            }

            async _resendWhatsappToCustomer() {
				const printer = new Printer(null, this.env.pos);
				const receiptString = this.orderReceiptWhatsApp.el.outerHTML;
                const ticketImage = await printer.htmlToImg(receiptString);
				const order = this.currentOrder;
				const client = this.props.client_whatsapp;//order.get_client();
				const orderName = order.get_name();
				const orderClient = { order_id: this.props.order_id, config_id: this.props.config_id, whatsapp: this.orderUiState.inputWhatsapp, message: this.orderUiState.inputMessage, name: client ? client.name : this.orderUiState.inputWhatsapp };			
				const order_server_id = this.env.pos.validated_orders_name_server_id_map[orderName];
				await this.rpc({
                    model: 'pos.order',
                    method: 'action_resend_whatsapp_to_customer',
                    args: [[order_server_id], orderName, orderClient, ticketImage],
					/*kwargs: { context: newContext },*/
                });
            }
			back() {
				this.props.resolve({ confirmed: true, payload: null });
				this.trigger('close-temp-screen');
			}
		}
		WaOrderReprintScreen.template = 'WaOrderReprintScreen';
		return WaOrderReprintScreen;
	};

	Registries.Component.addByExtending(WaOrderReprintScreen, ReceiptScreen);

	return WaOrderReprintScreen;
});
