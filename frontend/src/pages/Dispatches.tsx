import { useEffect, useState } from 'react';
import {
  Table,
  Tag,
  Space,
  Button,
  Modal,
  Typography,
  Descriptions,
  Timeline,
  message,
} from 'antd';
import {
  TruckOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons';
import { dispatchApi } from '../api';
import type { Dispatch, DispatchItem } from '../types';
import { DispatchStatus, BloodComponent } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const componentLabels: Record<BloodComponent, string> = {
  [BloodComponent.RBC]: '红细胞',
  [BloodComponent.PLASMA]: '血浆',
  [BloodComponent.PLATELET]: '血小板',
  [BloodComponent.CRYOPRECIPITATE]: '冷沉淀',
};

const statusColors: Record<DispatchStatus, string> = {
  [DispatchStatus.PREPARING]: 'orange',
  [DispatchStatus.IN_TRANSIT]: 'blue',
  [DispatchStatus.DELIVERED]: 'green',
};

const statusLabels: Record<DispatchStatus, string> = {
  [DispatchStatus.PREPARING]: '准备中',
  [DispatchStatus.IN_TRANSIT]: '运输中',
  [DispatchStatus.DELIVERED]: '已送达',
};

function Dispatches() {
  const [dispatches, setDispatches] = useState<Dispatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedDispatch, setSelectedDispatch] = useState<Dispatch | null>(null);
  const [coldChainRecords, setColdChainRecords] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await dispatchApi.getAll();
      setDispatches(res.data);
    } catch (error) {
      message.error('加载调拨单失败');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (dispatch: Dispatch) => {
    setSelectedDispatch(dispatch);
    try {
      const res = await dispatchApi.getById(dispatch.id);
      setSelectedDispatch(res.data);
      
      const coldChainRes = await fetch(`/api/v1/dispatches/${dispatch.id}/cold-chain`);
      const coldChainData = await coldChainRes.json();
      setColdChainRecords(coldChainData);
    } catch (error) {
      console.error('加载详情失败:', error);
    }
    setDetailVisible(true);
  };

  const handleStartTransit = async (id: string) => {
    try {
      await dispatchApi.startTransit(id);
      message.success('已开始运输');
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleConfirmDelivery = async (id: string) => {
    try {
      await dispatchApi.confirmDelivery(id);
      message.success('已确认送达');
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const columns = [
    {
      title: '调拨单号',
      dataIndex: 'dispatch_number',
      key: 'number',
      width: 160,
    },
    {
      title: '接收医院',
      key: 'hospital',
      render: (_: any, d: Dispatch) => d.hospital?.name,
      width: 140,
    },
    {
      title: '数量',
      dataIndex: 'total_units',
      key: 'units',
      width: 80,
      render: (v: number) => `${v} 单位`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (s: DispatchStatus) => (
        <Tag color={statusColors[s]} icon={<TruckOutlined />}>
          {statusLabels[s]}
        </Tag>
      ),
    },
    {
      title: '运输员',
      dataIndex: 'courier',
      key: 'courier',
      width: 100,
    },
    {
      title: '温度要求',
      dataIndex: 'temperature_requirement',
      key: 'temp',
      width: 150,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created',
      width: 160,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, d: Dispatch) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(d)}
          >
            详情
          </Button>
          {d.status === DispatchStatus.PREPARING && (
            <Button
              size="small"
              type="primary"
              icon={<TruckOutlined />}
              onClick={() => handleStartTransit(d.id)}
            >
              开始运输
            </Button>
          )}
          {d.status === DispatchStatus.IN_TRANSIT && (
            <Button
              size="small"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => handleConfirmDelivery(d.id)}
            >
              确认送达
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginTop: 0 }}>
        调拨管理
      </Title>

      <Table
        columns={columns}
        dataSource={dispatches}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1100 }}
      />

      <Modal
        title="调拨单详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {selectedDispatch && (
          <div>
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="调拨单号" span={1}>
                {selectedDispatch.dispatch_number}
              </Descriptions.Item>
              <Descriptions.Item label="状态" span={1}>
                <Tag color={statusColors[selectedDispatch.status]}>
                  {statusLabels[selectedDispatch.status]}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="接收医院" span={1}>
                {selectedDispatch.hospital?.name}
              </Descriptions.Item>
              <Descriptions.Item label="数量" span={1}>
                {selectedDispatch.total_units} 单位
              </Descriptions.Item>
              <Descriptions.Item label="运输员" span={1}>
                {selectedDispatch.courier || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="温度要求" span={1}>
                {selectedDispatch.temperature_requirement || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间" span={1}>
                {dayjs(selectedDispatch.created_at).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="送达时间" span={1}>
                {selectedDispatch.delivered_at
                  ? dayjs(selectedDispatch.delivered_at).format('YYYY-MM-DD HH:mm')
                  : '-'}
              </Descriptions.Item>
            </Descriptions>

            <Title level={5} style={{ marginBottom: 8 }}>
              血袋明细
            </Title>
            <Table
              size="small"
              columns={[
                {
                  title: '血袋编号',
                  key: 'bag',
                  render: (_: any, item: any) => item.blood_bag?.bag_number,
                },
                {
                  title: '血型',
                  key: 'bt',
                  render: (_: any, item: any) =>
                    `${item.blood_bag?.blood_type}${
                      item.blood_bag?.rh_type === 'POSITIVE' ? '+' : '-'
                    }`,
                },
                {
                  title: '成分',
                  key: 'comp',
                  render: (_: any, item: any) =>
                    componentLabels[item.blood_bag?.component],
                },
                {
                  title: '有效期',
                  key: 'expiry',
                  render: (_: any, item: any) =>
                    dayjs(item.blood_bag?.expiry_date).format('YYYY-MM-DD'),
                },
                {
                  title: '备注',
                  key: 'note',
                  render: (_: any, item: DispatchItem) =>
                    item.is_emergency_compatibility ? (
                      <Tag color="orange">紧急代偿</Tag>
                    ) : (
                      <Tag color="green">同型</Tag>
                    ),
                },
              ]}
              dataSource={selectedDispatch.items || []}
              rowKey="id"
              pagination={false}
              style={{ marginBottom: 16 }}
            />

            <Title level={5} style={{ marginBottom: 8 }}>
              冷链记录
            </Title>
            {coldChainRecords.length > 0 ? (
              <Timeline
                items={coldChainRecords.map((r) => ({
                  color:
                    r.temperature_celsius >= 2 && r.temperature_celsius <= 6
                      ? 'green'
                      : 'red',
                  children: (
                    <div>
                      <div>
                        <Text strong>
                          {dayjs(r.recorded_at).format('YYYY-MM-DD HH:mm')}
                        </Text>
                      </div>
                      <div>
                        <EnvironmentOutlined /> {r.location || '未知位置'}
                        {' | '}
                        温度:{' '}
                        <Text
                          strong
                          style={{
                            color:
                              r.temperature_celsius >= 2 &&
                              r.temperature_celsius <= 6
                                ? '#52c41a'
                                : '#ff4d4f',
                          }}
                        >
                          {r.temperature_celsius}°C
                        </Text>
                        {' | '}
                        操作员: {r.operator || '-'}
                      </div>
                      {r.notes && (
                        <div style={{ color: '#999' }}>{r.notes}</div>
                      )}
                    </div>
                  ),
                }))}
              />
            ) : (
              <Text type="secondary">暂无冷链记录</Text>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

export default Dispatches;
