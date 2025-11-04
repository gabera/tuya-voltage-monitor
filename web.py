#!/usr/bin/env python3
import os
from flask import Flask, render_template, jsonify, request
from database import VoltageDatabase
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db():
    """Get database connection"""
    return VoltageDatabase()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """
    Get voltage data with optional filtering
    Query params:
    - scale: hour, day, month (default: hour)
    - hours: number of hours to show (default: 24)
    - min_voltage: minimum voltage threshold (optional)
    - max_voltage: maximum voltage threshold (optional)
    - device_id: filter by specific device (optional)
    """
    db = get_db()

    scale = request.args.get('scale', 'hour')
    hours = int(request.args.get('hours', 24))
    min_voltage = request.args.get('min_voltage', type=float)
    max_voltage = request.args.get('max_voltage', type=float)
    device_id = request.args.get('device_id')

    # Calculate time window
    time_window = datetime.now() - timedelta(hours=hours)

    # Build query based on scale
    if scale == 'hour':
        # Hourly aggregation
        query = """
        SELECT
            device_id,
            DATE_TRUNC('hour', timestamp) as time_bucket,
            AVG(voltage) as avg_voltage,
            MIN(voltage) as min_voltage,
            MAX(voltage) as max_voltage,
            COUNT(*) as reading_count
        FROM voltage_readings
        WHERE timestamp >= %s
        """
    elif scale == 'day':
        # Daily aggregation
        query = """
        SELECT
            device_id,
            DATE_TRUNC('day', timestamp) as time_bucket,
            AVG(voltage) as avg_voltage,
            MIN(voltage) as min_voltage,
            MAX(voltage) as max_voltage,
            COUNT(*) as reading_count
        FROM voltage_readings
        WHERE timestamp >= %s
        """
    elif scale == 'month':
        # Monthly aggregation
        query = """
        SELECT
            device_id,
            DATE_TRUNC('month', timestamp) as time_bucket,
            AVG(voltage) as avg_voltage,
            MIN(voltage) as min_voltage,
            MAX(voltage) as max_voltage,
            COUNT(*) as reading_count
        FROM voltage_readings
        WHERE timestamp >= %s
        """
    else:
        # Raw data (no aggregation)
        query = """
        SELECT
            device_id,
            timestamp as time_bucket,
            voltage as avg_voltage,
            voltage as min_voltage,
            voltage as max_voltage,
            1 as reading_count
        FROM voltage_readings
        WHERE timestamp >= %s
        """

    params = [time_window]

    # Add voltage filters
    if min_voltage is not None:
        query += " AND voltage >= %s"
        params.append(min_voltage)

    if max_voltage is not None:
        query += " AND voltage <= %s"
        params.append(max_voltage)

    # Add device filter
    if device_id:
        query += " AND device_id = %s"
        params.append(device_id)

    # Complete query
    if scale in ['hour', 'day', 'month']:
        query += " GROUP BY device_id, time_bucket"

    query += " ORDER BY time_bucket ASC"

    try:
        with db.conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        # Format results
        data = []
        for row in rows:
            data.append({
                'device_id': row[0],
                'timestamp': row[1].isoformat() if row[1] else None,
                'avg_voltage': float(row[2]) if row[2] else None,
                'min_voltage': float(row[3]) if row[3] else None,
                'max_voltage': float(row[4]) if row[4] else None,
                'count': row[5]
            })

        db.close()
        return jsonify({
            'success': True,
            'data': data,
            'scale': scale,
            'hours': hours
        })

    except Exception as e:
        db.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices')
def get_devices():
    """Get list of all devices"""
    db = get_db()

    query = """
    SELECT DISTINCT device_id
    FROM voltage_readings
    ORDER BY device_id
    """

    try:
        with db.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        devices = [row[0] for row in rows]
        db.close()

        return jsonify({
            'success': True,
            'devices': devices
        })

    except Exception as e:
        db.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    db = get_db()

    query = """
    SELECT
        device_id,
        COUNT(*) as total_readings,
        AVG(voltage) as avg_voltage,
        MIN(voltage) as min_voltage,
        MAX(voltage) as max_voltage,
        MIN(timestamp) as first_reading,
        MAX(timestamp) as last_reading
    FROM voltage_readings
    GROUP BY device_id
    ORDER BY device_id
    """

    try:
        with db.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        stats = []
        for row in rows:
            stats.append({
                'device_id': row[0],
                'total_readings': row[1],
                'avg_voltage': float(row[2]) if row[2] else None,
                'min_voltage': float(row[3]) if row[3] else None,
                'max_voltage': float(row[4]) if row[4] else None,
                'first_reading': row[5].isoformat() if row[5] else None,
                'last_reading': row[6].isoformat() if row[6] else None
            })

        db.close()
        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        db.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
