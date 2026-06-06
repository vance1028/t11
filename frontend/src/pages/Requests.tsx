import { useEffect, useState } from 'react';
import {
  Table,
  Tag,
  Space,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Typography,
  Descriptions,
  Row,
  Col,
  Card,
} from 'antd';
import {
  PlusOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { requestApi, hospitalApi, dispatchApi } from '../api';
import type { BloodRequest, MatchResult, MatchResultItem, Hospital } from '../types';
import {
  BloodType,
  RhType,
  BloodComponent,
  UrgencyLevel,
  RequestStatus,
} from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;

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

const statusColors: Record<RequestStatus, string> = {
  [RequestStatus.PENDING]: 'default',
  [RequestStatus.PARTIAL_MATCHED]: 'orange',
  [RequestStatus.FULLY_MATCHED]: 'green',
  [RequestStatus.DISPATCHED]: 'blue',
  [RequestStatus.CANCELLED]: 'red',
};

const statusLabels: Record<RequestStatus, string> = {
  [RequestStatus.PENDING]: '待匹配',
  [RequestStatus.PARTIAL_MATCHED]: '部分匹配',
  [RequestStatus.FULLY_MATCHED]: '完全匹配',
  [RequestStatus.DISPATCHED]: '已出库',
  [RequestStatus.CANCELLED]: '已取消',
};

function Requests() {
  const [requests, setRequests] = useState<BloodRequest[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [matchModalVisible, setMatchModalVisible] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<BloodRequest | null>(null);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [reqRes, hospRes] = await Promise.all([
        requestApi.getAll(),
        hospitalApi.getAll(),
      ]);
      setRequests(reqRes.data);
      setHospitals(hospRes.data.filter((h) => !h.is_blood_center));
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await requestApi.create(values);
      message.success('申请已提交');
      setCreateVisible(false);
      form.resetFields();
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '提交失败');
    }
  };

  const handleMatch = async (request: BloodRequest) => {
    setSelectedRequest(request);
    try {
      const res = await requestApi.match(request.id);
      setMatchResult(res.data);
      setSelectedItems(new Set(res.data.matched_items.map((i) => i.blood_bag_id)));
      setMatchModalVisible(true);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '匹配失败');
    }
  };

  const handleConfirmDispatch = async () => {
    if (!selectedRequest || !matchResult) return;

    const items = matchResult.matched_items.filter((i) =>
      selectedItems.has(i.blood_bag_id)
    );

    if (items.length === 0) {
      message.error('请至少选择一袋');
      return;
    }

    try {
      await dispatchApi.confirm(selectedRequest.id, items);
      message.success('调拨已确认，库存已扣减');
      setMatchModalVisible(false);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '确认失败');
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await requestApi.cancel(id);
      message.success('已取消');
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消失败');
    }
  };

  const columns = [
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
      title: '患者信息',
      key: 'patient',
      width: 120,
      render: (_: any, r: BloodRequest) => (
        <div>
          <div>{r.patient_name || '未填写'}</div>
          <div style={{ fontSize: '12px', color: '#999' }}>
            {r.patient_age ? `${r.patient_age}岁` : ''}
          </div>
        </div>
      ),
    },
    {
      title: '血型/成分',
      key: 'info',
      width: 130,
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
      key: 'qty',
      width: 90,
      render: (_: any, r: BloodRequest) => (
        <span>
          {r.matched_units}/{r.quantity_units}
        </span>
      ),
    },
    {
      title: '紧急程度',
      dataIndex: 'urgency',
      key: 'urgency',
      width: 80,
      render: (u: UrgencyLevel) => (
        <Tag color={urgencyColors[u]}>{urgencyLabels[u]}</Tag>
      ),
      sorter: (a, b) => {
        const order = { EMERGENCY: 0, URGENT: 1, ROUTINE: 2 };
        return order[a.urgency] - order[b.urgency];
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (s: RequestStatus) => (
        <Tag color={statusColors[s]}>{statusLabels[s]}</Tag>
      ),
    },
    {
      title: '申请时间',
      dataIndex: 'requested_at',
      key: 'time',
      width: 160,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_: any, r: BloodRequest) => (
        <Space>
          {r.status === RequestStatus.PENDING ||
          r.status === RequestStatus.PARTIAL_MATCHED ? (
            <Button
              size="small"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => handleMatch(r)}
            >
              匹配配血
            </Button>
          ) : null}
          {r.status === RequestStatus.PENDING ? (
            <Button
              size="small"
              danger
              icon={<CloseCircleOutlined />}
              onClick={() => handleCancel(r.id)}
            >
              取消
            </Button>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginTop: 0 }}>
        用血申请
      </Title>

      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateVisible(true)}
        >
          新建申请
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={requests}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1100 }}
      />

      <Modal
        title="新建用血申请"
        open={createVisible}
        onCancel={() => setCreateVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            label="申请医院"
            name="hospital_id"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择医院">
              {hospitals.map((h) => (
                <Option key={h.id} value={h.id}>
                  {h.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="患者血型"
                name="patient_blood_type"
                rules={[{ required: true }]}
              >
                <Select>
                  {Object.values(BloodType).map((bt) => (
                    <Option key={bt} value={bt}>
                      {bt}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Rh"
                name="patient_rh_type"
                rules={[{ required: true }]}
              >
                <Select>
                  <Option value={RhType.POSITIVE}>Rh+</Option>
                  <Option value={RhType.NEGATIVE}>Rh-</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="成分"
                name="component"
                rules={[{ required: true }]}
              >
                <Select>
                  {Object.entries(componentLabels).map(([key, label]) => (
                    <Option key={key} value={key}>
                      {label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="数量(单位)"
                name="quantity_units"
                rules={[{ required: true }]}
                initialValue={2}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="紧急程度"
                name="urgency"
                rules={[{ required: true }]}
                initialValue={UrgencyLevel.ROUTINE}
              >
                <Select>
                  {Object.entries(urgencyLabels).map(([key, label]) => (
                    <Option key={key} value={key}>
                      {label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="患者姓名" name="patient_name">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="年龄" name="patient_age">
                <InputNumber min={0} max={150} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="诊断" name="diagnosis">
            <Input />
          </Form.Item>
          <Form.Item label="备注" name="notes">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交申请
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="配血结果"
        open={matchModalVisible}
        onCancel={() => setMatchModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setMatchModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="confirm"
            type="primary"
            onClick={handleConfirmDispatch}
            disabled={selectedItems.size === 0}
          >
            确认调拨 (已选 {selectedItems.size} 袋)
          </Button>,
        ]}
      >
        {selectedRequest && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Descriptions column={3} size="small">
              <Descriptions.Item label="申请编号">
                {selectedRequest.request_number}
              </Descriptions.Item>
              <Descriptions.Item label="医院">
                {selectedRequest.hospital?.name}
              </Descriptions.Item>
              <Descriptions.Item label="血型/成分">
                {selectedRequest.patient_blood_type}
                {selectedRequest.patient_rh_type === 'POSITIVE' ? '+' : '-'}{' '}
                {componentLabels[selectedRequest.component]}
              </Descriptions.Item>
              <Descriptions.Item label="需求量">
                {selectedRequest.quantity_units} 单位
              </Descriptions.Item>
              <Descriptions.Item label="已匹配">
                {selectedRequest.matched_units} 单位
              </Descriptions.Item>
              <Descriptions.Item label="紧急程度">
                <Tag color={urgencyColors[selectedRequest.urgency]}>
                  {urgencyLabels[selectedRequest.urgency]}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {matchResult && (
          <div>
            <div style={{ marginBottom: 8 }}>
              <Text type="secondary">
                共找到 {matchResult.total_matched} 袋匹配血液
                {matchResult.is_fully_matched ? '，可完全满足需求' : '，库存不足'}
              </Text>
            </div>
            <Table
              size="small"
              rowSelection={{
                selectedRowKeys: Array.from(selectedItems),
                onChange: (keys) => setSelectedItems(new Set(keys as string[])),
                getCheckboxProps: (record: MatchResultItem) => ({
                  defaultChecked: true,
                }),
              }}
              columns={[
                {
                  title: '血袋编号',
                  dataIndex: 'bag_number',
                  key: 'bag_number',
                },
                {
                  title: '血型',
                  key: 'bt',
                  render: (_: any, r: MatchResultItem) =>
                    `${r.blood_type}${r.rh_type === 'POSITIVE' ? '+' : '-'}`,
                },
                {
                  title: '成分',
                  dataIndex: 'component',
                  key: 'component',
                  render: (c: BloodComponent) => componentLabels[c],
                },
                {
                  title: '有效期至',
                  key: 'expiry',
                  render: (_: any, r: MatchResultItem) => (
                    <span
                      style={{
                        color:
                          r.days_to_expiry <= 1 ? '#ff4d4f' : 'inherit',
                      }}
                    >
                      {dayjs(r.expiry_date).format('YYYY-MM-DD')} (剩
                      {r.days_to_expiry}天)
                    </span>
                  ),
                },
                {
                  title: '备注',
                  key: 'note',
                  render: (_: any, r: MatchResultItem) =>
                    r.is_emergency_compatibility ? (
                      <Tag color="orange">紧急代偿</Tag>
                    ) : (
                      <Tag color="green">同型</Tag>
                    ),
                },
              ]}
              dataSource={matchResult.matched_items}
              rowKey="blood_bag_id"
              pagination={false}
            />
          </div>
        )}
      </Modal>
    </div>
  );
}

export default Requests;
