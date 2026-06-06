import { useEffect, useState } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Space,
  Alert,
  Typography,
} from 'antd';
import {
  WarningOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  TruckOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { dashboardApi, inventoryApi } from '../api';
import type { DashboardStats, InventoryStats, BloodRequest } from '../types';
import { BloodComponent, UrgencyLevel } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const componentLabels: Record<BloodComponent, string> = {
  [BloodComponent.RBC]: '红细胞',
  [BloodComponent.PLASMA]: '血浆',
  [BloodComponent.PLATELET]: '血小板',
  [BloodComponent.CRYOPRECIPITATE]: '冷沉淀',
};

const urgencyColors: Record<UrgencyLevel, string> = {
  [UrgencyLevel.ROUTINE]: 'blue',
  [UrgencyLevel.URGENT]: 'orange',
  [UrgencyLevel.EMERGENCY]: 'red',
};

const urgencyLabels: Record<UrgencyLevel, string> = {
  [UrgencyLevel.ROUTINE]: '常规',
  [UrgencyLevel.URGENT]: '紧急',
  [UrgencyLevel.EMERGENCY]: '抢救',
};

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [expiringAlerts, setExpiringAlerts] = useState<any[]>([]);
  const [expiredAlerts, setExpiredAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, expiringRes, expiredRes] = await Promise.all([
        dashboardApi.getStats(),
        inventoryApi.getExpiringSoon(),
        inventoryApi.getExpired(),
      ]);
      setStats(statsRes.data);
      setExpiringAlerts(expiringRes.data);
      setExpiredAlerts(expiredRes.data);
    } catch (error) {
      console.error('加载看板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const inventoryColumns = [
    {
      title: '成分',
      dataIndex: 'component',
      key: 'component',
      render: (c: BloodComponent) => componentLabels[c],
      width: 100,
    },
    {
      title: '血型',
      key: 'bloodType',
      width: 80,
      render: (_: any, record: InventoryStats) =>
        `${record.blood_type}${record.rh_type === 'POSITIVE' ? '+' : '-'}`,
    },
    {
      title: '库存总量',
      dataIndex: 'total_units',
      key: 'total',
      width: 90,
      render: (v: number) => (
        <Text strong style={{ fontSize: '16px' }}>
          {v}
        </Text>
      ),
    },
    {
      title: '临期预警',
      dataIndex: 'expiring_soon',
      key: 'expiring',
      width: 90,
      render: (v: number) =>
        v > 0 ? (
          <Tag color="orange" icon={<WarningOutlined />}>
            {v} 袋
          </Tag>
        ) : (
          <Text type="secondary">0</Text>
        ),
    },
    {
      title: '已过期',
      dataIndex: 'expired',
      key: 'expired',
      width: 90,
      render: (v: number) =>
        v > 0 ? (
          <Tag color="red" icon={<ExclamationCircleOutlined />}>
            {v} 袋
          </Tag>
        ) : (
          <Text type="secondary">0</Text>
        ),
    },
  ];

  const urgentRequestColumns = [
    {
      title: '申请编号',
      dataIndex: 'request_number',
      key: 'number',
      width: 140,
    },
    {
      title: '医院',
      key: 'hospital',
      render: (_: any, r: BloodRequest) => r.hospital?.name,
      width: 120,
    },
    {
      title: '紧急程度',
      dataIndex: 'urgency',
      key: 'urgency',
      width: 80,
      render: (u: UrgencyLevel) => (
        <Tag color={urgencyColors[u]}>{urgencyLabels[u]}</Tag>
      ),
    },
    {
      title: '血型/成分',
      key: 'info',
      width: 120,
      render: (_: any, r: BloodRequest) => (
        <span>
          {r.patient_blood_type}
          {r.patient_rh_type === 'POSITIVE' ? '+' : '-'}{' '}
          {componentLabels[r.component]}
        </span>
      ),
    },
    {
      title: '需求量',
      dataIndex: 'quantity_units',
      key: 'qty',
      width: 70,
      render: (v: number) => `${v} 单位`,
    },
    {
      title: '申请时间',
      dataIndex: 'requested_at',
      key: 'time',
      width: 160,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
  ];

  const plateletCritical =
    stats?.inventory_by_type.filter(
      (i) => i.component === BloodComponent.PLATELET && i.total_units <= 2
    ) || [];

  return (
    <div>
      <Title level={3} style={{ marginTop: 0 }}>
        库存总览看板
      </Title>

      {plateletCritical.length > 0 && (
        <Alert
          message="⚠️ 血小板库存告急！"
          description={plateletCritical
            .map(
              (p) =>
                `${p.blood_type}${p.rh_type === 'POSITIVE' ? '+' : '-'} 仅剩 ${p.total_units} 单位`
            )
            .join('；')}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {expiredAlerts.length > 0 && (
        <Alert
          message={`⚠️ 发现 ${expiredAlerts.length} 袋已过期血液待报废`}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {expiringAlerts.filter((a) => a.level === 'critical').length > 0 && (
        <Alert
          message={`⚠️ 发现 ${expiringAlerts.filter((a) => a.level === 'critical').length} 袋血液即将过期（1天内），请优先调度`}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="库存总袋数"
              value={stats?.total_inventory || 0}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待处理申请"
              value={stats?.total_requests_pending || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="运输中调拨"
              value={stats?.total_dispatches_in_transit || 0}
              prefix={<TruckOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="临期预警"
              value={stats?.expiring_soon_count || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#cf1322' }}
              suffix="袋"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card
            title={
              <Space>
                <DatabaseOutlined />
                库存详情
              </Space>
            }
          >
            <Table
              columns={inventoryColumns}
              dataSource={stats?.inventory_by_type || []}
              rowKey={(r) => `${r.component}-${r.blood_type}-${r.rh_type}`}
              size="small"
              pagination={false}
              scroll={{ y: 320 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            title={
              <Space>
                <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
                紧急/抢救申请
              </Space>
            }
          >
            <Table
              columns={urgentRequestColumns}
              dataSource={stats?.urgent_requests || []}
              rowKey="id"
              size="small"
              pagination={false}
              scroll={{ y: 320 }}
              locale={{ emptyText: '暂无紧急申请' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;
