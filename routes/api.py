from flask import Blueprint, request, jsonify, session, make_response
from datetime import datetime
import json

from models.vehicle_model import db, Vehicle, Prediction, Alert
from models.ml_engine import ml_engine

api = Blueprint('api', __name__)


def get_current_user_id():
    return session.get('user_id')


# ─── Vehicle CRUD ────────────────────────────────────────────────────────────

@api.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    vehicles = Vehicle.query.filter_by(user_id=user_id).all()
    return jsonify({'vehicles': [v.to_dict() for v in vehicles]})


@api.route('/api/vehicles', methods=['POST'])
def add_vehicle():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    vehicle = Vehicle(
        user_id=user_id,
        vehicle_number=data.get('vehicle_number', ''),
        vehicle_model=data.get('vehicle_model', ''),
        manufacturer=data.get('manufacturer', ''),
        mileage=float(data.get('mileage', 0)),
        engine_temp=float(data.get('engine_temp', 90)),
        oil_quality=float(data.get('oil_quality', 80)),
        tire_pressure=float(data.get('tire_pressure', 32)),
        brake_condition=float(data.get('brake_condition', 80)),
        battery_health=float(data.get('battery_health', 85)),
        fuel_efficiency=float(data.get('fuel_efficiency', 30)),
        service_history=int(data.get('service_history', 1)),
        last_service_date=data.get('last_service_date', '')
    )
    db.session.add(vehicle)
    db.session.commit()

    # Auto-run prediction after adding
    prediction_data = _run_prediction(vehicle, data)
    return jsonify({'success': True, 'vehicle': vehicle.to_dict(), 'prediction': prediction_data}), 201


@api.route('/api/vehicles/<int:vid>', methods=['GET'])
def get_vehicle(vid):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    vehicle = Vehicle.query.filter_by(id=vid, user_id=user_id).first_or_404()
    return jsonify({'vehicle': vehicle.to_dict()})


@api.route('/api/vehicles/<int:vid>', methods=['PUT'])
def update_vehicle(vid):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    vehicle = Vehicle.query.filter_by(id=vid, user_id=user_id).first_or_404()
    data = request.get_json()
    for field in ['mileage', 'engine_temp', 'oil_quality', 'tire_pressure',
                  'brake_condition', 'battery_health', 'fuel_efficiency',
                  'service_history', 'last_service_date']:
        if field in data:
            setattr(vehicle, field, data[field])
    vehicle.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'vehicle': vehicle.to_dict()})


@api.route('/api/vehicles/<int:vid>', methods=['DELETE'])
def delete_vehicle(vid):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    vehicle = Vehicle.query.filter_by(id=vid, user_id=user_id).first_or_404()
    Prediction.query.filter_by(vehicle_id=vid).delete()
    Alert.query.filter_by(vehicle_id=vid).delete()
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({'success': True})


# ─── Prediction Engine ───────────────────────────────────────────────────────

def _run_prediction(vehicle: Vehicle, raw_data: dict) -> dict:
    """Run ML prediction and save result."""
    result = ml_engine.predict(raw_data)

    prediction = Prediction(
        vehicle_id=vehicle.id,
        health_score=result['health_score'],
        maintenance_required=result['maintenance_required'],
        risk_level=result['risk_level'],
        urgency=result['urgency'],
        failure_components=json.dumps([result['failure_component']]),
        recommendations=json.dumps(result['recommendations']),
        estimated_cost=result['estimated_cost'],
        accuracy=result['accuracy']
    )
    db.session.add(prediction)

    # Create alerts for critical items
    if result['urgency'] in ('CRITICAL', 'HIGH'):
        severity = 'CRITICAL' if result['urgency'] == 'CRITICAL' else 'WARNING'
        msg = f"Vehicle {vehicle.vehicle_number}: {result['failure_component']} detected. Urgency: {result['urgency']}"
        alert = Alert(vehicle_id=vehicle.id, message=msg, severity=severity)
        db.session.add(alert)

    db.session.commit()
    return result


@api.route('/api/vehicles/<int:vid>/predict', methods=['POST'])
@api.route('/api/vehicle/<int:vid>/predict', methods=['POST'])
def predict(vid):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    vehicle = Vehicle.query.filter_by(id=vid, user_id=user_id).first_or_404()

    data = request.get_json() or {}
    # Merge saved vehicle data with any overrides from request
    vehicle_data = vehicle.to_dict()
    vehicle_data.update(data)

    result = _run_prediction(vehicle, vehicle_data)
    return jsonify({'prediction': result})


@api.route('/api/predict/quick', methods=['POST'])
def quick_predict():
    """Run prediction on raw form data without saving."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    # Save vehicle and predict
    vehicle = Vehicle(
        user_id=user_id,
        vehicle_number=data.get('vehicle_number', 'TEMP-001'),
        vehicle_model=data.get('vehicle_model', 'Unknown'),
        manufacturer=data.get('manufacturer', 'Unknown'),
        mileage=float(data.get('mileage', 0)),
        engine_temp=float(data.get('engine_temp', 90)),
        oil_quality=float(data.get('oil_quality', 80)),
        tire_pressure=float(data.get('tire_pressure', 32)),
        brake_condition=float(data.get('brake_condition', 80)),
        battery_health=float(data.get('battery_health', 85)),
        fuel_efficiency=float(data.get('fuel_efficiency', 30)),
        service_history=int(data.get('service_history', 1)),
        last_service_date=data.get('last_service_date', '')
    )
    db.session.add(vehicle)
    db.session.commit()

    result = _run_prediction(vehicle, data)
    return jsonify({'prediction': result, 'vehicle_id': vehicle.id, 'vehicle': vehicle.to_dict()})


# ─── Predictions History ─────────────────────────────────────────────────────

@api.route('/api/vehicles/<int:vid>/predictions', methods=['GET'])
def get_predictions(vid):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    vehicle = Vehicle.query.filter_by(id=vid, user_id=user_id).first_or_404()
    preds = Prediction.query.filter_by(vehicle_id=vid).order_by(Prediction.created_at.desc()).limit(20).all()
    return jsonify({'predictions': [p.to_dict() for p in preds]})


# ─── Alerts ──────────────────────────────────────────────────────────────────

@api.route('/api/alerts', methods=['GET'])
def get_alerts():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    vehicle_ids = [v.id for v in Vehicle.query.filter_by(user_id=user_id).all()]
    alerts = Alert.query.filter(Alert.vehicle_id.in_(vehicle_ids)).order_by(Alert.created_at.desc()).limit(20).all()
    return jsonify({'alerts': [a.to_dict() for a in alerts]})


@api.route('/api/alerts/<int:aid>/read', methods=['POST'])
def mark_alert_read(aid):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    alert = Alert.query.get_or_404(aid)
    alert.is_read = True
    db.session.commit()
    return jsonify({'success': True})


# ─── Dashboard Analytics ─────────────────────────────────────────────────────

@api.route('/api/dashboard', methods=['GET'])
def dashboard():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    vehicles = Vehicle.query.filter_by(user_id=user_id).all()
    total = len(vehicles)

    if total == 0:
        return jsonify({
            'total_vehicles': 0,
            'avg_health': 0,
            'critical_count': 0,
            'ok_count': 0,
            'trend': ml_engine.get_trend_data(),
            'risk_distribution': {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        })

    health_scores = []
    risk_dist = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
    for v in vehicles:
        latest = Prediction.query.filter_by(vehicle_id=v.id).order_by(Prediction.created_at.desc()).first()
        if latest:
            health_scores.append(latest.health_score)
            risk_dist[latest.risk_level] = risk_dist.get(latest.risk_level, 0) + 1

    avg_health = round(sum(health_scores) / len(health_scores), 1) if health_scores else 0
    critical = risk_dist.get('CRITICAL', 0) + risk_dist.get('HIGH', 0)

    return jsonify({
        'total_vehicles': total,
        'avg_health': avg_health,
        'critical_count': critical,
        'ok_count': total - critical,
        'trend': ml_engine.get_trend_data(),
        'risk_distribution': risk_dist
    })


# ─── PDF Report ──────────────────────────────────────────────────────────────

@api.route('/api/vehicles/<int:vid>/report', methods=['GET'])
def export_pdf(vid):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    vehicle = Vehicle.query.filter_by(id=vid, user_id=user_id).first_or_404()
    latest_pred = Prediction.query.filter_by(vehicle_id=vid).order_by(Prediction.created_at.desc()).first()

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import inch
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20, textColor=colors.HexColor('#00d4ff'), spaceAfter=12)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#8b5cf6'), spaceAfter=6)
        normal_style = styles['Normal']

        story.append(Paragraph("VMPS — Vehicle Maintenance Prediction Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", normal_style))
        story.append(Spacer(1, 0.3*inch))

        story.append(Paragraph("Vehicle Information", heading_style))
        vehicle_data_rows = [
            ['Field', 'Value'],
            ['Vehicle Number', vehicle.vehicle_number],
            ['Model', vehicle.vehicle_model],
            ['Manufacturer', vehicle.manufacturer],
            ['Mileage', f"{vehicle.mileage:,.0f} km"],
            ['Engine Temperature', f"{vehicle.engine_temp}°C"],
            ['Oil Quality', f"{vehicle.oil_quality}%"],
            ['Tire Pressure', f"{vehicle.tire_pressure} PSI"],
            ['Brake Condition', f"{vehicle.brake_condition}%"],
            ['Battery Health', f"{vehicle.battery_health}%"],
            ['Fuel Efficiency', f"{vehicle.fuel_efficiency} km/L"],
            ['Last Service', vehicle.last_service_date or 'N/A'],
        ]
        tbl = Table(vehicle_data_rows, colWidths=[2.5*inch, 4*inch])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a0f1e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#00d4ff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.3*inch))

        if latest_pred:
            pred_dict = latest_pred.to_dict()
            story.append(Paragraph("AI Prediction Results", heading_style))
            pred_rows = [
                ['Metric', 'Value'],
                ['Health Score', f"{pred_dict['health_score']}%"],
                ['Maintenance Required', 'YES' if pred_dict['maintenance_required'] else 'NO'],
                ['Risk Level', pred_dict['risk_level']],
                ['Service Urgency', pred_dict['urgency']],
                ['Failure Component', pred_dict['failure_components'][0] if pred_dict['failure_components'] else 'None'],
                ['Estimated Cost', f"${pred_dict['estimated_cost']:,.2f}"],
                ['Prediction Accuracy', f"{pred_dict['accuracy']}%"],
            ]
            tbl2 = Table(pred_rows, colWidths=[2.5*inch, 4*inch])
            tbl2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a0f1e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            story.append(tbl2)
            story.append(Spacer(1, 0.3*inch))

            if pred_dict['recommendations']:
                story.append(Paragraph("Recommended Actions", heading_style))
                for rec in pred_dict['recommendations']:
                    story.append(Paragraph(f"• {rec.get('action', '')} [{rec.get('priority', '')}] — Est. cost: ${rec.get('cost', 0)}", normal_style))

        doc.build(story)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=VMPS_Report_{vehicle.vehicle_number}.pdf'
        return response

    except ImportError:
        return jsonify({'error': 'ReportLab not installed. Run: pip install reportlab'}), 500


# ─── Chatbot ─────────────────────────────────────────────────────────────────

@api.route('/api/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    message = data.get('message', '').lower()

    responses = {
        'oil': "Engine oil should be changed every 5,000-10,000 km or when oil quality drops below 30%. Low oil quality leads to increased friction and engine wear.",
        'brake': "Brake pads typically last 40,000-70,000 km. Replace them when brake condition drops below 30%. Listen for squealing sounds as an indicator.",
        'battery': "Car batteries last 3-5 years. A battery health below 50% indicates it may need replacement soon. Cold weather accelerates battery degradation.",
        'tire': "Maintain tire pressure at 30-35 PSI. Check monthly and inflate to manufacturer specifications. Under/over-inflation reduces fuel efficiency.",
        'engine': "Keep engine temperature between 85-100°C. Temperatures above 110°C indicate coolant or radiator issues. Check coolant levels regularly.",
        'fuel': "Poor fuel efficiency may indicate dirty fuel injectors, a clogged air filter, or worn spark plugs. Service typically improves efficiency by 10-15%.",
        'service': "Regular service intervals: every 6 months or 10,000 km. A complete service includes oil change, filter replacement, brake inspection, and tire rotation.",
        'predict': "To get an AI prediction, fill in the vehicle form on the left with your current sensor readings and click 'Analyze Vehicle'.",
        'hello': "Hello! I'm VMPS AI Assistant. I can help you with vehicle maintenance questions, diagnosis tips, and service recommendations!",
        'hi': "Hi there! How can I help you with your vehicle maintenance today?",
        'help': "I can answer questions about: oil changes, brake maintenance, battery health, tire pressure, engine temperature, fuel efficiency, and service schedules.",
    }

    reply = None
    for key, response in responses.items():
        if key in message:
            reply = response
            break

    if not reply:
        if any(w in message for w in ['cost', 'price', 'expensive']):
            reply = "Typical maintenance costs: Oil change ($50-100), Brake pads ($150-300), Battery replacement ($100-200), Full service ($200-400). Preventive maintenance saves 40% compared to reactive repairs."
        elif any(w in message for w in ['urgent', 'critical', 'emergency']):
            reply = "For CRITICAL urgency: Stop driving immediately and contact a mechanic. Continued driving with critical issues can lead to complete vehicle failure or safety hazards."
        else:
            reply = "I'm here to help with vehicle maintenance questions! Ask me about oil, brakes, battery, tires, engine, or fuel efficiency. You can also type 'help' for a list of topics."

    return jsonify({'reply': reply, 'timestamp': datetime.utcnow().isoformat()})
