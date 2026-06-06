import { useState } from 'react';
import {
  Card,
  Form,
  Select,
  Button,
  Result,
  Row,
  Col,
  Typography,
  Table,
  Tag,
  message,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { compatibilityApi } from '../api';
import {
  BloodType,
  RhType,
  BloodComponent,
} from '../types';

const { Title, Text } = Typography;
const { Option } = Select;

const componentLabels: Record<BloodComponent, string> = {
  [BloodComponent.RBC]: '红细胞',
  [BloodComponent.PLASMA]: '血浆',
  [BloodComponent.PLATELET]: '血小板',
  [BloodComponent.CRYOPRECIPITATE]: '冷沉淀',
};

function Compatibility() {
  const [form] = Form.useForm();
  const [result, setResult] = useState<any>(null);
  const [compatibleDonors, setCompatibleDonors] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleCheck = async (values: any) => {
    setLoading(true);
    try {
      const res = await compatibilityApi.check(values);
      setResult(res.data);

      const donorsRes = await compatibilityApi.getCompatibleDonors({
        recipient_blood_type: values.recipient_blood_type,
        recipient_rh_type: values.recipient_rh_type,
        component: values.component,
        is_emergency: values.is_emergency || false,
      });
      setCompatibleDonors(donorsRes.data);
    } catch (error) {
      message.error('检查失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3} style={{ marginTop: 0 }}>
        <ExperimentOutlined /> 血型相容性检查
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={10}>
          <Card title="相容性查询">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleCheck}
              initialValues={{
                component: BloodComponent.RBC,
                is_emergency: false,
              }}
            >
              <Title level={5} type="secondary">
                供血者
              </Title>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="ABO 血型"
                    name="donor_blood_type"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      {Object.values(BloodType).map((bt) => (
                        <Option key={bt} value={bt}>
                          {bt} 型
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Rh 血型"
                    name="donor_rh_type"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value={RhType.POSITIVE}>Rh 阳性 (+)</Option>
                      <Option value={RhType.NEGATIVE}>Rh 阴性 (-)</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Title level={5} type="secondary" style={{ marginTop: 8 }}>
                受血者
              </Title>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="ABO 血型"
                    name="recipient_blood_type"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      {Object.values(BloodType).map((bt) => (
                        <Option key={bt} value={bt}>
                          {bt} 型
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Rh 血型"
                    name="recipient_rh_type"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value={RhType.POSITIVE}>Rh 阳性 (+)</Option>
                      <Option value={RhType.NEGATIVE}>Rh 阴性 (-)</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="血液成分" name="component">
                <Select>
                  {Object.entries(componentLabels).map(([key, label]) => (
                    <Option key={key} value={key}>
                      {label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item label="是否紧急抢救" name="is_emergency" valuePropName="checked">
                <Select>
                  <Option value={false}>否（常规）</Option>
                  <Option value={true}>是（紧急/抢救）</Option>
                </Select>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  loading={loading}
                  size="large"
                >
                  检查相容性
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} md={14}>
          {result && (
            <Card title="检查结果" style={{ marginBottom: 16 }}>
              <Result
                status={result.is_compatible ? 'success' : 'error'}
                icon={
                  result.is_compatible ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                  )
                }
                title={
                  result.is_compatible ? (
                    <span style={{ color: '#52c41a' }}>
                      {result.is_emergency_use ? '紧急情况下相容' : '完全相容'}
                    </span>
                  ) : (
                    <span style={{ color: '#ff4d4f' }}>不相容，禁止输注</span>
                  )
                }
                subTitle={
                  <div>
                    <div>
                      供血: <Text strong>{result.donor_blood_type}</Text>
                      {result.donor_rh_type === 'POSITIVE' ? ' Rh+' : ' Rh-'}{' '}
                      {componentLabels[result.component]}
                    </div>
                    <div>
                      受血: <Text strong>{result.recipient_blood_type}</Text>
                      {result.recipient_rh_type === 'POSITIVE' ? ' Rh+' : ' Rh-'}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      匹配优先级: <Text strong>{result.priority_score}</Text> 分
                    </div>
                    {result.is_emergency_use && (
                      <Tag color="orange" style={{ marginTop: 8 }}>
                        ⚠️ 仅供紧急情况使用
                      </Tag>
                    )}
                  </div>
                }
              />
            </Card>
          )}

          {compatibleDonors.length > 0 && (
            <Card title="可输注的供血者血型列表（按优先级排序）">
              <Table
                size="small"
                columns={[
                  {
                    title: '血型',
                    key: 'bt',
                    width: 120,
                    render: (_: any, r: any) => (
                      <Text strong>
                        {r.blood_type}
                        {r.rh_type === 'POSITIVE' ? ' Rh+' : ' Rh-'}
                      </Text>
                    ),
                  },
                  {
                    title: '优先级',
                    dataIndex: 'priority_score',
                    key: 'priority',
                    width: 100,
                    render: (v: number) => `${v} 分`,
                  },
                  {
                    title: '备注',
                    key: 'note',
                    render: (_: any, r: any) =>
                      r.is_emergency_use ? (
                        <Tag color="orange">紧急代偿</Tag>
                      ) : (
                        <Tag color="green">优选同型</Tag>
                      ),
                  },
                ]}
                dataSource={compatibleDonors}
                rowKey={(r) => `${r.blood_type}-${r.rh_type}`}
                pagination={false}
              />
            </Card>
          )}

          {!result && (
            <Card>
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                <ExperimentOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>请在左侧填写信息查询相容性</div>
                <div style={{ fontSize: 12, marginTop: 8 }}>
                  本系统遵循临床输血技术规范，同型优先，紧急情况下启用相容性代偿
                </div>
              </div>
            </Card>
          )}
        </Col>
      </Row>

      <Card title="输血相容性规则说明" style={{ marginTop: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Title level={5}>红细胞 (RBC)</Title>
            <ul>
              <li>O 型红细胞为万能供血者，可输给任何血型</li>
              <li>AB 型为万能受血者，可接受任何血型红细胞</li>
              <li>Rh 阴性血可给 Rh 阳性或阴性患者</li>
              <li>Rh 阳性血只能给 Rh 阳性患者（紧急除外）</li>
            </ul>
          </Col>
          <Col xs={24} md={12}>
            <Title level={5}>血浆 / 冷沉淀</Title>
            <ul>
              <li>AB 型血浆为万能血浆，可输给任何血型</li>
              <li>O 型血浆只能给 O 型患者</li>
              <li>A 型血浆可给 A、AB 型患者</li>
              <li>B 型血浆可给 B、AB 型患者</li>
            </ul>
          </Col>
          <Col xs={24} md={12}>
            <Title level={5}>血小板 (PLATELET)</Title>
            <ul>
              <li>优先 ABO 同型输注</li>
              <li>紧急情况下可跨 ABO 血型输注</li>
              <li>Rh 阴性血小板优先给 Rh 阴性患者</li>
            </ul>
          </Col>
          <Col xs={24} md={12}>
            <Title level={5} style={{ color: '#ff4d4f' }}>
              ⚠️ 重要说明
            </Title>
            <ul>
              <li>本系统仅供参考，实际输血必须做交叉配血试验</li>
              <li>紧急代偿输注需经主治医师同意并记录</li>
              <li>Rh 阴性育龄期女性尽量避免 Rh 阳性血液</li>
            </ul>
          </Col>
        </Row>
      </Card>
    </div>
  );
}

export default Compatibility;
