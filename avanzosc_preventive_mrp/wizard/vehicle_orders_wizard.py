# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2012 Daniel (Avanzosc) <http://www.avanzosc.com>
#    15/12/2011
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the  GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import fields, osv
from tools.translate import _
import wizard
import pooler
import time        
class wizard_preventive_operations(wizard.interface):    
       
    _inherit = "wizard_preventive_operations"
    
    def _create_vehicle_prev_op (self, cr, uid, data, context):
        if context is None:
            context = {}
        value = {}
        pool = pooler.get_pool(cr.dbname)
        operation_obj =  pool.get('preventive.operations')
        operation = operation_obj.browse(cr, uid, data['id'])
        
        exists = pool.get('mrp.repair').search(cr,uid,[('prevop','=', ope.id)])
        if not exists:
            ope_name = ope.name           
            vehi_id = ope.vehicle.id
            products = ope.material
            if vehi_id > 0:
                vehicle= pool.get('fleet.vehicles').browse(cr, uid,vehi_id)        
                product_id = vehicle.product_id.id
                if product_id != False: 
                    product_obj= pool.get('product.product').browse(cr,uid,product_id)
                    location_from = vehicle.location        
                    location_to = pool.get ('stock.location').search(cr,uid,[('name', 'like', 'Taller')])
                    pool.get('fleet.vehicles').write(cr, uid, [vehi_id],{ 'location': location_to[0]})
                    move_id = pool.get('stock.move').create(cr,uid,{ 
                          'product_id' : product_id, 
                          'name' : product_obj.name + '=> Taller',
                          'location_id' : location_from.id,
                          'location_dest_id': location_to[0],
                          'product_uom': product_obj.product_tmpl_id.uom_id.id,
                          })    
                    repair = pool.get('mrp.repair').create(cr,uid,{'name':  pool.get('ir.sequence').get(cr, uid, 'mrp.repair'), 'location_id' : location_from.id, 'location_dest_id' :  location_to[0], 'move_id' : move_id, 'product_id': product_id, 'preventive' : 1, 'idvehicle':vehi_id, 'prevop':ope.id })
                    for product in products:
                        p_id = product.product_id
                        p_name = p_id.name
                        p_price = p_id.lst_price
                        p_uom = product.product_uom.id
                        p_qty = product.product_uom_qty
                        pool.get('mrp.repair.line').create(cr,uid,{'repair_id':repair, 'name': p_name, 'product_id': p_id.id, 'product_uom_qty': p_qty, 'price_unit': p_price, 'product_uom': p_uom, 'to_invoice': 0, 'type':'add', 'state':'draft', 'move_id':move_id, 'location_id' : location_from.id, 'location_dest_id' :  location_to[0]})
                    
                    value = {
                            'name': _('Create Order'),
                            'view_type': 'form',
                            'view_mode': 'form,tree',
                            'res_model': 'mrp.repair',
                            'res_id': int(repair),
                            'view_id': False,
                            'context': context,
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'nodestroy': True
                            }
            pre_pro=pool.get('preventive.proceed').search(cr,uid,[('prevname','=', ope.id)])
            pool.get('preventive.proceed').write(cr, uid, [pre_pro[0]], {'order':repair,'dateorder':time.strftime('%Y-%m-%d')})
        else:
            raise osv.except_osv(_('Error!'),_('There is already an order created for this operation.'))       
        return value
    
    
wizard_preventive_operations('create.order.wizard.new')('create.order.wizard.new')
