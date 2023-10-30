odoo.define('whatsapp_pos_integration.ReceiptScreen', function(require) {
    'use strict';

    const { useRef } = owl.hooks;
    //const { is_whatsapp } = require('web.utils');
    //const { useErrorHandlers, onChangeOrder } = require('point_of_sale.custom_hooks');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');

    const WhatsappReceiptScreen = ReceiptScreen =>
        class extends ReceiptScreen {
            constructor() {
                super(...arguments);
                //onChangeOrder(null, (newOrder) => newOrder && this.render());
				this.orderReceiptWhatsApp = useRef('order-receipt');
				//const order = this.currentOrder;
                //const client = order.get_client();
                const order = this.currentOrder;
                const client = order.get_client();
                this.orderUiState = useContext(order.uiState.ReceiptScreen);
				const orderName = order.get_name();
				const pos_config = this.env.pos.config;
				let message = pos_config.whatsapp_default_message.replace("_CUSTOMER_", client && client.name || 'Customer');
				//console.log('==WhatsappReceiptScreen=1=',order)
                this.orderUiState = useContext(order.uiState.ReceiptScreen);
                this.orderUiState.inputWhatsapp = this.orderUiState.inputWhatsapp || (client && client.whatsapp) || '';
                this.orderUiState.inputMessage = message + ' ' + orderName +'.';
				//setTimeout(async () => await this.onSendWhatsapp(), 0);
                //console.log('==WhatsappReceiptScreen=1=',this.orderReceiptWhatsApp.el.outerHTML)
				//console.log('==WhatsappReceiptScreen=2=',this.orderReceiptWhatsApp.el,this.orderReceiptWhatsApp)
				if ((this.orderReceiptWhatsApp) && (this.orderUiState.inputWhatsapp || this.orderUiState.inputWhatsapp != '0')) {
                    setTimeout(async () => await this.onSendWhatsapp(), 20);
                }
            }
            /**
             * @override
             */

			/*whenClosing() {
                this.orderDone();
            }*/
            async onSendWhatsapp() {
                if (!this.orderUiState.inputWhatsapp) {
                    this.orderUiState.whatsappSuccessful = false;
                    this.orderUiState.whatsappNotice = this.env._t('Whatsapp number is empty.');
                    return;
                }
                try {
					console.log('==SEND==')
                    await this._sendWhatsappToCustomer();
                    this.orderUiState.whatsappSuccessful = true;
                    this.orderUiState.whatsappNotice = 'Whatsapp sent.'
                } catch (error) {
					console.log('==ERROR==',error)
                    this.orderUiState.whatsappSuccessful = false;
                    this.orderUiState.whatsappNotice = 'Sending Whatsapp failed. Please try again.'
                }
            }


            async _sendWhatsappToCustomer() {
				//const printer = new Printer(null, this.env.pos);
                //const order = this.currentOrder;
                const printer = new Printer(null, this.env.pos);
                //this.ticketString = ticket;
                //console.log('===orderReceiptWhatsApp=11==',this.orderReceiptWhatsApp.el.outerHTML)
                //const receiptString = this.ticketString.el.outerHTML;
                const receiptString = this.orderReceiptWhatsApp.el.outerHTML;
                const ticketImage = await printer.htmlToImg(receiptString);
				const order = this.currentOrder;
				const client = order.get_client();
				const orderName = order.get_name();
				const orderClient = { order: order, whatsapp: this.orderUiState.inputWhatsapp, message: this.orderUiState.inputMessage, name: client ? client.name : this.orderUiState.inputWhatsapp };
				const order_server_id = this.env.pos.validated_orders_name_server_id_map[orderName];
				await this.rpc({
                    model: 'pos.order',
                    method: 'action_send_whatsapp_to_customer',
                    args: [[order_server_id], orderName, orderClient, ticketImage],
                });
            }
        };
	Registries.Component.extend(ReceiptScreen, WhatsappReceiptScreen);
	//Registries.Component.addByExtending(ReceiptScreen, AbstractReceiptScreen);
    //Registries.Component.extend(ReceiptScreen, ReceiptScreen);

    return ReceiptScreen;
});
